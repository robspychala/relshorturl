from google.appengine.ext import db

class User(db.Model):
  ref = db.StringProperty()
  created_date = db.DateTimeProperty(auto_now_add=True)

class Url(db.Model):
  user = db.ReferenceProperty(User)  
  longurl = db.StringProperty(required=True)
  userip = db.StringProperty()
  created_date = db.DateTimeProperty(auto_now_add=True)