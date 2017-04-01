from google.appengine.ext import ndb

class Like(ndb.Model):
    like_blog = ndb.KeyProperty(kind='Blog')
    like_user = ndb.KeyProperty(kind='User')
    like_dislike = ndb.IntegerProperty(required=True)
