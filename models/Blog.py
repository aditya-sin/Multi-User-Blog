import os
import jinja2
from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class Blog(ndb.Model):
    """ This class creates an entity Blog which stores
    the details of blogs submitted by users.
    """
    blog_author = ndb.KeyProperty(kind='User')
    subject = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)
    blog_comments = ndb.KeyProperty(kind='Comment', repeated=True)
    blog_likes = ndb.KeyProperty(kind='Like', repeated=True)

    def render(self, **kw):
        # Allows correct rendering of new line in the blog
        self._render_text = self.content.replace('\n', '<br>')
        count_comment = 0
        count_like = 0
        count_dislike = 0
        id_blog = self.key.id()
        comments = ndb.get_multi(self.blog_comments)
        likes = self.blog_likes

        for l in likes:
            if l.get().like_dislike == 1:
                count_like += 1
            elif l.get().like_dislike == 0:
                count_dislike += 1
        
        count_comment = len(comments)
        id_blog = str(id_blog)+'-0'
        return render_str("post.html", p=self, comments=comments,
                          count_comment=count_comment,
                          count_like=count_like, count_dislike=count_dislike,
                          id_blog=id_blog, **kw)

    # Finds an entity of kind Blog using its id and returns it
    @classmethod
    def by_id(cls, uid):
        return Blog.get_by_id(uid)
