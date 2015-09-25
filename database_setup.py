########## Header ##########
import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
Base = declarative_base()
############################

########## Body ##########
#User table - to store user information
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer,primary_key = True)
    name = Column(String(100),nullable=False)
    email = Column(String(250))
    picture = Column(String(10))
    updated_on = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    created_on = Column(DateTime,default=datetime.datetime.now())

#Catagory table - to store created catagories. 
class Catagory(Base):
    __tablename__ = 'catagory'
    id = Column(Integer,primary_key = True)
    name = Column(String(250),nullable=False)
    description = Column(String(250))
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)
    updated_on = Column(DateTime,default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    created_on = Column(DateTime,default=datetime.datetime.now())
    
    @property
    def serialize(self):
        return {
            'id'            : self.id,
            'name'          : self.name,
            'description'   : self.description,
            'updated_on'    : self.updated_on,
            'created_on'    : self.created_on,
            'created_by'    : self.user.name,
            }
#Product table - to store created products.
class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer,primary_key = True)
    name = Column(String(100),nullable=False)
    description = Column(String(250))
    price = Column(String(10))
    flavour = Column(String(250))
    image = Column(String(250))
    catagory_id = Column(Integer,ForeignKey('catagory.id'))
    catagory = relationship(Catagory)
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)
    updated_on = Column(DateTime,default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    created_on = Column(DateTime,default=datetime.datetime.now())
    

    @property
    def serialize(self):
        return {
            'id'            : self.id,
            'name'          : self.name,
            'description'   : self.description,
            'price'         : self.price,
            'flavour'       : self.flavour,
            'catagory_id'   : self.catagory.id,
            'catagory'      : self.catagory.name,
            'updated_on'    : self.updated_on,
            'created_on'    : self.created_on,
            'created_by'    : self.user.name,
            }
    
############################

########## Footer ##########
engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
############################
