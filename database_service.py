#This file contains reusable method to perform database transactions
#import necessary libraries, tables and database file
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base,Catagory,Product,User
from sqlalchemy import desc
from flask import jsonify
import os
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

#Method to create new catagory
def NewCatagory(c_name,c_desc,c_user_id):
    item = Catagory(name = c_name,description=c_desc,user_id=c_user_id)
    session.add(item)
    session.commit()

#Method to retrieve catagory by catagory ID
def GetCatagoryByID(cid):
    item = session.query(Catagory).filter_by(id=cid).one()
    return item

#Method to get all catagories
def GetAllCatagory():
    item = session.query(Catagory).all()
    return item

#Method to modify catagory
def EditCatagory(cid,c_name,c_desc):
    item = session.query(Catagory).filter_by(id=cid).one()
    item.name = c_name
    item.description = c_desc
    session.add(item)
    session.commit()

#Method to delete catagory
def DeleteCatagory(cid):
    item = session.query(Catagory).filter_by(id=cid).one()
    session.delete(item)
    session.commit()

#Method to get 10 latest products to display on home page
def GetLatestProduct():
    item = session.query(Product).order_by(desc(Product.created_on)).limit(10).all()
    return item

#Method to get all products:
def GetAllProducts():
    item = session.query(Product).all()
    return item

#Method to create new product
def NewProduct(p_name,p_desc,p_price,p_flavour,p_path,cid,c_user_id):
    item = Product(name = p_name,description=p_desc, price=p_price, flavour=p_flavour,image=p_path,catagory_id=cid,user_id=c_user_id)
    session.add(item)
    session.commit()

#Method to retrieve product by selected catagory
def GetProductByCatagory(cid):
    item = session.query(Product).filter_by(catagory_id=cid).all()
    return item

#Method to retrive product information by product ID
def GetProductByID(pid):
    item = session.query(Product).filter_by(id=pid).one()
    return item

#Method to modify product
def EditProduct(pid,p_name,p_desc,p_price,p_flavour,p_image,cid):
    item = session.query(Product).filter_by(id=pid).one()
    item.name = p_name
    item.description = p_desc
    item.price = p_price
    item.flavour = p_flavour
    #only update the image URL when user uploaded a new image for it
    if p_image:
        item.image = p_image
    item.catagory_id=cid
    session.add(item)
    session.commit()

#Method to delete product
def DeleteProduct(pid):
    item = session.query(Product).filter_by(id=pid).one()
    session.delete(item)
    session.commit()
    #also remove the image in /static/uploads folder when the product is deleted
    os.remove(item.image)

#Method to create user and return it's local user ID
def CreateUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

#Method to get user information by user ID
def GetUserInfobyID(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

#Method to get user ID from it's email address
def GetUserIDbyEmail(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

#Method to check if the user already exist in our database
#If user does not exist, create the user in our database and return it's local user ID
#If user exists, return it's local user ID
def CheckUserExist(login_session):
    user_id = GetUserIDbyEmail(login_session['email'])
    if not user_id:
        user_id = CreateUser(login_session)
    return user_id

#Method to check if the user is the owner of the catagory
#Only permits user to modify the catagory if they are the creator of it
def hasCatagoryPermission(cid,c_user_id):
    catagory = session.query(Catagory).filter_by(id=cid).one()
    if catagory.user_id == c_user_id:
        return True
    else:
        return False
    
#Method to check if the user is the owner of the product
#Only permits user to modify the product if they are the creator of it
def hasProductPermission(pid,p_user_id):
    product = session.query(Product).filter_by(id=pid).one()
    if product.user_id == p_user_id:
        return True
    else:
        return False

#API Endpoint Methods

#JSON
#Method to get all catagories
def GetAllCatagoryJSON():
    try:
        catagory = GetAllCatagory()
        if catagory is not None:
            return jsonify(Catagory=[i.serialize for i in catagory])
        else:
            return jsonify(Catagory='')
    except:
        return jsonify(Catagory='')

#Method to get specified catagories
def GetCatagorybyIDJSON(cid):
    try:
        catagory = GetCatagoryByID(cid)
        if catagory is not None:
            return jsonify(Catagory=catagory.serialize)
        else:
            return jsonify(Catagory='')
    except:
        return jsonify(Catagory='')

#Method to get all products
def GetAllProductsJSON():
    try:
        products = GetAllProducts()
        if products is not None:
            return jsonify(Product=[i.serialize for i in products])
        else:
            return jsonify(Product='')
    except:
        return jsonify(Product='')

#Method to get product by catagory
def GetProductbyCatagoryJSON(cid):
    try:
        products = GetProductByCatagory(cid)
        if products is not None:
            return jsonify(Product=[i.serialize for i in products])
        else:
            return jsonify(Product='')
    except:
        return jsonify(Product='')

#Method to get product by product id
def GetProductbyIDJSON(pid):
    try:
        product = GetProductByID(pid)
        if product is not None:
            return jsonify(Product=product.serialize)
        else:
            return jsonify(Product='')
    except:
        return jsonify(Product='')

#XML
#Method to get all catagories
def GetAllCatagoryXML():
    catagory = GetAllCatagory()
    xml = parseCatagoryXML(catagory,'ALL')
    print xml
    return xml     

#Method to get specified catagories
def GetCatagorybyIDXML(cid):
    catagory = GetCatagoryByID(cid)
    xml = parseCatagoryXML(catagory,'ONE')
    return xml

#Method to get all products
def GetAllProductsXML():
    products = GetAllProducts()
    xml = parseProductXML(products,'ALL')
    return xml

#Method to get product by catagory
def GetProductbyCatagoryXML(cid):
    products = GetProductByCatagory(cid,'ALL')
    xml = parseProductXML(products)
    return xml

#Method to get product by product id
def GetProductbyIDXML(pid):
    product = GetProductByID(pid,'ONE')
    xml = parseProductXML(product)
    return xml

#Method to parse catagory to XML format
def parseCatagoryXML(catagory,query_type):
    xml = ''
    xml += '<Catalog>'
    if query_type == 'ALL':
        for item in catagory:
            xml += '<catagory>'
            xml += '<id>%s</id>' %item.id
            xml += '<name>%s</name>' %item.name
            xml += '<description>%s</description>' %item.description
            xml += '<updated_on>%s</updated_on>' %item.updated_on
            xml += '<created_on>%s</created_on>' %item.created_on
            xml += '<created_by>%s</created_by>' %item.user.name
            xml += '</catagory>'
    else:
        xml += '<catagory>'
        xml += '<id>%s</id>' %catagory.id
        xml += '<name>%s</name>' %catagory.name
        xml += '<description>%s</description>' %catagory.description
        xml += '<updated_on>%s</updated_on>' %catagory.updated_on
        xml += '<created_on>%s</created_on>' %catagory.created_on
        xml += '<created_by>%s</created_by>' %catagory.user.name
        xml += '</catagory>'
    xml += '</Catalog>'
    return xml

#Method to parse product to XML format
def parseProductXML(products,query_type):
    xml = ''
    xml += '<Catalog>'
    if query_type == 'ALL':
        for item in products:
            xml += '<product>'
            xml += '<id>%s</id>' %item.id
            xml += '<name>%s</name>' %item.name
            xml += '<description>%s</description>' %item.description
            xml += '<price>%s</price>' %item.price
            xml += '<flavour>%s</flavour>' %item.flavour
            xml += '<catagory_id>%s</catagory_id>' %item.catagory.id
            xml += '<catagory>%s</catagory>' %item.catagory.name
            xml += '<updated_on>%s</updated_on>' %item.updated_on
            xml += '<created_on>%s</created_on>' %item.created_on
            xml += '<created_by>%s</created_by>' %item.user.name
            xml += '</product>'
    else:
        xml += '<product>'
        xml += '<id>%s</id>' %products.id
        xml += '<name>%s</name>' %products.name
        xml += '<description>%s</description>' %products.description
        xml += '<price>%s</price>' %products.price
        xml += '<flavour>%s</flavour>' %products.flavour
        xml += '<catagory_id>%s</catagory_id>' %products.catagory.id
        xml += '<catagory>%s</catagory>' %products.catagory.name
        xml += '<updated_on>%s</updated_on>' %products.updated_on
        xml += '<created_on>%s</created_on>' %products.created_on
        xml += '<created_by>%s</created_by>' %products.user.name
        xml += '</product>'
    xml += '</Catalog>'
    return xml
    
