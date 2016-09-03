from google.appengine.ext import db

# Comments Entity
class Comment(db.Model):
    post_id = db.IntegerProperty(required=True)
    owner = db.StringProperty(required=True)
    text = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

# Votes Entity
class Votes(db.Model):
    post_id = db.IntegerProperty(required=True)
    votedby = db.IntegerProperty(required=True)
    votetype = db.IntegerProperty(default=0)
    
class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    salt = db.StringProperty(required=True)
    email = db.StringProperty
    score = 0

    @classmethod
    def get_name_by_id(cls, uid):
        user = User.get_by_id(uid)
        if user:
            return user.username

    @classmethod
    def get_id_by_name(cls, name):
        user = User.all().filter('username =', name).get()
        if user:
            return user.key().id()

class Blog(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    owner = db.IntegerProperty(required=True)
    score = db.IntegerProperty(default=0)