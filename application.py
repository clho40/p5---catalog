#import all necessary libraries and also the database servce module
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask import session as login_session
from flask import make_response
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import random,string
import database_service
import requests
import os
from werkzeug import secure_filename
from flask.ext.seasurf import SeaSurf

#define flask application
app = Flask(__name__)

#Cross-Site request forgery implementation
csrf = SeaSurf(app)

#define the upload destination
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#define the allowed uploaded files extensions. Only images!
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg', 'gif'])

#loads google api client secret - to obtain access to the API
CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id']

#Method to check if the uploaded file is in acceptable image format
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

#Method to check if user is already logged in
def CheckUserLoggedIn():
    user_loggedin = False
    if 'username' in login_session:
        user_loggedin = True
    return user_loggedin

#Method to get user's username by checking if user is already logged in
def getSessionUsername():
    username = ''
    if CheckUserLoggedIn():
        username = login_session['username']
    return username

#Method to get user's user ID by checking if user is already logged in
def getSessionUserID():
    user_id = ''
    if CheckUserLoggedIn():
        user_id = login_session['user_id']
    return user_id

#Method to get user's picture by checking if user is already logged in
def getSessionUserPic():
    pic = ''
    if CheckUserLoggedIn():
        pic = login_session['picture']
    return pic

#Homepage - Display 10 latest products
@csrf.exempt
@app.route('/')
def IndexPage():
    catagories = database_service.GetAllCatagory()
    logged_in = CheckUserLoggedIn()
    username = getSessionUsername()
    picture = getSessionUserPic()
    products = database_service.GetLatestProduct()
    user_id = getSessionUserID()
    return render_template('index.html',catagories=catagories,logged_in=logged_in,username=username,picture=picture,products=products,user_id=user_id)

#New Catagory page - A page that contains a form to create a new catagory
@app.route('/catagory/new', methods=['GET','POST'])
def newCatagory():
    #Direct user to login page if not logged in. User must be logged in before creating catagories.
    logged_in = CheckUserLoggedIn()
    if not logged_in:
        return redirect('/login')
    username = getSessionUsername()
    catagories = database_service.GetAllCatagory()
    picture = getSessionUserPic()
    if request.method == 'POST':
        #When user clicks the submit button, create new catagory entry into our database
        user_id=getSessionUserID()
        database_service.NewCatagory(request.form['name'],request.form['desc'],user_id)
        flash('New catagory created!','alert-success')
        return redirect(url_for('newCatagory'))
    else:
        #When the page loads, load the newcatagory.html page
        return render_template('newcatagory.html',catagories=catagories,logged_in=logged_in,username=username,picture=picture)

#Edit Catagory page - A page that contains a form for user to modify catagory
@app.route('/catagory/<int:cid>/edit', methods=['GET','POST'])
def editCatagory(cid):
    #Direct user to login page if not logged in. User must be logged in before modifying catagories.
    logged_in = CheckUserLoggedIn()
    if not logged_in:
        return redirect('/login')
    username = getSessionUsername()
    user_id=getSessionUserID()
    catagories = database_service.GetAllCatagory()
    picture = getSessionUserPic()
    #Check if the user is the owner of this catagory. Allow user to modify if they are the creator of it.
    if database_service.hasCatagoryPermission(cid,user_id):
        if request.method == 'POST':
            #When user clicks the submit button, updates catagory information into our database
            database_service.EditCatagory(cid,request.form['name'],request.form['desc'])
            flash('Catagory updated!','alert-success')
            return redirect(url_for('showProducts',cid=cid))
        else:
            #When the page loads, load the editcatagory.html page
            sel_catagory = database_service.GetCatagoryByID(cid)
            return render_template('editcatagory.html',catagories=catagories,sel_catagory=sel_catagory,logged_in=logged_in,username=username,picture=picture)
    else:
        #User is NOT the owner of this catagory. Show red alert message and redirect back to product page
        flash('No permission to modify this catagory!','alert-danger')
        return redirect(url_for('showProducts',cid=cid))

#Delete Catagory page - A confirmation page for user to delete catagory
@app.route('/catagory/<int:cid>/delete', methods=['GET','POST'])
def deleteCatagory(cid):
    logged_in = CheckUserLoggedIn()
    if not logged_in:
        return redirect('/login')
    username = getSessionUsername()
    user_id=getSessionUserID()
    catagories = database_service.GetAllCatagory()
    picture = getSessionUserPic()
    #Check if the user is the owner of this catagory. Allow user to delete if they are the creator of it.
    if database_service.hasCatagoryPermission(cid,user_id):
        if request.method == 'POST':
            #When user clicks the Yes button, delete the catagory from our database
            database_service.DeleteCatagory(cid)
            flash('Catagory deleted!','alert-success')
            return redirect(url_for('IndexPage'))
        else:
            #When the page loads, load the deletecatagory.html page
            sel_catagory = database_service.GetCatagoryByID(cid)
            return render_template('deletecatagory.html',catagories=catagories,sel_catagory=sel_catagory,logged_in=logged_in,username=username,picture=picture)
    else:
        #User is NOT the owner of this catagory. Show red alert message and redirect back to product page
        flash('No permission to delete this catagory!','alert-danger')
        return redirect(url_for('showProducts',cid=cid))

#Display products page - A page to show all the products correspond to the selected catagory
@csrf.exempt
@app.route('/catagory/<int:cid>')
def showProducts(cid):
    username = getSessionUsername()
    catagories = database_service.GetAllCatagory()
    sel_catagory = database_service.GetCatagoryByID(cid)
    products = database_service.GetProductByCatagory(cid)
    user_id = getSessionUserID()
    logged_in = CheckUserLoggedIn()
    picture = getSessionUserPic()
    return render_template('products.html',catagories=catagories,sel_catagory=sel_catagory, products=products,logged_in=logged_in,username=username,user_id=user_id,picture=picture)

#New Product page - A page that contains a form to create a new product
@app.route('/product/new', methods=['GET','POST'])
def newProduct():
    #Direct user to login page if not logged in. User must be logged in before creating products.
    logged_in = CheckUserLoggedIn()
    if not logged_in:
        return redirect('/login')
    username = getSessionUsername()
    catagories = database_service.GetAllCatagory()
    picture = getSessionUserPic()
    if request.method == 'POST':
        #When user clicks the submit button
        #get the uploaded image information
        pic_path = ''
        file = request.files['file']
        if file and allowed_file(file.filename):
            #if there are image uploaded, save into /static/uploads
            filename = secure_filename(file.filename)
            pic_path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
            file.save(pic_path)
        #create the new product entry into our database
        user_id = getSessionUserID()
        database_service.NewProduct(request.form['name'],request.form['desc'],request.form['price'],request.form['flavour'],pic_path,request.form['catagory'],user_id)
        flash('New product created!','alert-success')
        return redirect(url_for('newProduct'))
    else:
        return render_template('newproduct.html',catagories=catagories,logged_in=logged_in,username=username,picture=picture)

#Edit Product page - A page that contains a form for user to modify products
@app.route('/catagory/<int:cid>/product/<int:pid>/edit', methods=['GET','POST'])
def editProduct(cid,pid):
    #Direct user to login page if not logged in. User must be logged in before modifying products.
    logged_in = CheckUserLoggedIn()
    if not logged_in:
        return redirect('/login')
    username = getSessionUsername()
    user_id=getSessionUserID()
    catagories = database_service.GetAllCatagory()
    picture = getSessionUserPic()
    #Check if the user is the owner of this catagory. Allow user to modify if they are the creator of it.
    if database_service.hasProductPermission(pid,user_id):
        if request.method == 'POST':
            #When user clicks the submit button
            pic_path = ''
            file = request.files['file']
            if file and allowed_file(file.filename):
                #if there are new image uploaded, save into /static/uploads
                filename = secure_filename(file.filename)
                pic_path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
                file.save(pic_path)
            #update the modified product detail into our database
            database_service.EditProduct(pid,request.form['name'],request.form['desc'],request.form['price'],request.form['flavour'],pic_path,request.form['catagory'])
            flash('Product updated!','alert-success')
            return redirect(url_for('showProducts',cid=cid))
        else:
            sel_catagory = database_service.GetCatagoryByID(cid)
            sel_product = database_service.GetProductByID(pid)
            return render_template('editproduct.html',catagories=catagories,sel_catagory=sel_catagory, sel_product=sel_product,logged_in=logged_in,username=username,picture=picture)
    else:
        #User is NOT the owner of this product. Show red alert message and redirect back to product page
        flash('No permission to modify this product!','alert-danger')
        return redirect(url_for('showProducts',cid=cid))

#Delete Product page - A confirmation page for user to delete products
@app.route('/catagory/<int:cid>/product/<int:pid>/delete', methods=['GET','POST'])
def deleteProduct(cid,pid):
    #Check if the user is the owner of this product. Allow user to delete if they are the creator of it.
    logged_in = CheckUserLoggedIn()
    if not logged_in:
        return redirect('/login')
    username = getSessionUsername()
    user_id=getSessionUserID()
    catagories = database_service.GetAllCatagory()
    picture = getSessionUserPic()
    #Check if the user is the owner of this product. Allow user to delete if they are the creator of it.
    if database_service.hasProductPermission(pid,user_id):
        if request.method == 'POST':
            #When user clicks the Yes button, delete the product along with it's image from our database
            database_service.DeleteProduct(pid)
            flash('Product deleted!','alert-success')
            return redirect(url_for('showProducts',cid=cid))
        else:
            sel_catagory = database_service.GetCatagoryByID(cid)
            sel_product = database_service.GetProductByID(pid)
            return render_template('deleteproduct.html',catagories=catagories,sel_catagory=sel_catagory,sel_product=sel_product,logged_in=logged_in,username=username,picture=picture)
    else:
        flash('No permission to delete this product!','alert-danger')
        return redirect(url_for('showProducts',cid=cid))

#Show login page when user clicks Login button
@csrf.exempt
@app.route('/login')
def showLogin():
    logged_in = CheckUserLoggedIn()
    picture = getSessionUserPic()
    if logged_in:
        username = getSessionUsername()
        flash('You are already logged in as %s' %username,'alert-success')
        return redirect(url_for('IndexPage'))
    catagories = database_service.GetAllCatagory()
    #Generate state key
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html',catagories=catagories, STATE=state,picture=picture)

#login using google plus account
@csrf.exempt
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),200)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['user_id'] = database_service.CheckUserExist(login_session)
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'],'alert-success')
    print "done!"
    return output

#disconnect(Logout) google plus account
@csrf.exempt
@app.route("/gdisconnect")
def gdisconnect():
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected'),401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' %access_token
    h = httplib2.Http()
    result = h.request(url,'GET')[0]

    if result['status'] == '200':
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        flash('Successfully Logout','alert-success')
        return redirect(url_for('IndexPage'))
    else:
        flash('Failed to revoke token for given user.','alert-danger')
        return redirect(url_for('IndexPage'))

#Login using facebook account
@csrf.exempt
@app.route("/fbconnect", methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    login_session['user_id'] =  database_service.CheckUserExist(login_session)

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'], 'alert-success')
    return output

#Disconnect(Logout) from facebook account
@csrf.exempt
@app.route("/fbdisconnect", methods=['POST'])
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    url = 'https://graph.facebook.com/%s/permissions' %facebook_id
    h=httplib2.Http()
    result = h.request(url,'DELETE')[1]
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    del login_session['facebook_id']
    flash('Successfully Disconnected','alert-success')
    #response = make_response(json.dumps('Successfully disconnected'),200)
    #response.headers['Content-Type'] = 'application/json'
    return redirect(url_for('IndexPage'))

#Fired when Logout button is clicked. Check which provider user used to login and perform disconnect
@app.route('/disconnect')
@csrf.exempt
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
        if login_session['provider'] == 'facebook':
            fbdisconnect()
    return redirect(url_for('IndexPage'))

#Get user thumbnail picture
def getThumbnail():
    if 'picture' in login_session:
        return login_session['picture']
    
#API END POINT

#JSON
#Get all catalog catagories
@app.route('/catagory/all/JSON')
def JSONGetAllCatagory():
    json = database_service.GetAllCatagoryJSON()
    return json

#Get catalog by catalog id
@app.route('/catagory/<int:cid>/JSON')
def JSONGetCatagoryByID(cid):
    json = database_service.GetCatagorybyIDJSON(cid)
    return json

#Get all products
@app.route('/product/all/JSON')
def JSONGetAllProducts():
    json = database_service.GetAllProductsJSON()
    return json

#Get product by catagory
@app.route('/catagory/<int:cid>/product/all/JSON')
def JSONGetProductbyCatagory(cid):
    json = database_service.GetProductbyCatagoryJSON(cid)
    return json

#Get product by product id
@app.route('/product/<int:pid>/JSON')
def JSONGetProductByID(pid):
    json = database_service.GetProductbyIDJSON(pid)
    return json

#XML
#Get all catalog catagories
@app.route('/catagory/all/XML')
def XMLGetAllCatagory():
    xml = database_service.GetAllCatagoryXML()
    response = make_response(xml)
    response.headers['Content-Type'] = 'application/xml'
    return response

#Get catalog by catalog id
@app.route('/catagory/<int:cid>/XML')
def XMLGetCatagoryByID(cid):
    xml = database_service.GetCatagorybyIDXML(cid)
    response = make_response(xml)
    response.headers['Content-Type'] = 'application/xml'
    return response

#Get all products
@app.route('/product/all/XML')
def XMLGetAllProducts():
    xml = database_service.GetAllProductsXML()
    response = make_response(xml)
    response.headers['Content-Type'] = 'application/xml'
    return response

#Get product by catagory
@app.route('/catagory/<int:cid>/product/all/XML')
def XMLGetProductbyCatagory(cid):
    xml = database_service.GetProductbyCatagoryXML(cid)
    response = make_response(xml)
    response.headers['Content-Type'] = 'application/xml'
    return response

#Get product by product id
@app.route('/product/<int:pid>/XML')
def XMLGetProductByID(pid):
    xml = database_service.GetProductbyIDXML(pid)
    response = make_response(xml)
    response.headers['Content-Type'] = 'application/xml'
    return response
    
if __name__ == '__main__':
    app.secret_key = 'Ae00QqjmTKFlVkgqgRKNtQg5Nk2pm8VQZjdaP+qDtms='
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)



