from google.appengine.ext import ndb

class Comment(ndb.Model):
    comment_blog = ndb.KeyProperty(kind='Blog')
    user_name = ndb.KeyProperty(kind='User')
    comment_content = ndb.StringProperty(required=True)
    comment_time = ndb.DateTimeProperty(auto_now_add=True)
    comment_id = ndb.StringProperty()

    # Finds an entity of kind Comment using its id and returns it
    @classmethod
    def by_id(cls, uid):
        return Comment.get_by_id(uid)
