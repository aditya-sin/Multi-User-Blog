from handlers import BlogHandler
from models import Blog
from google.appengine.ext import ndb


class Posts(BlogHandler):
    """ If the user is login it displays the blog posts
    of only that particular user, otherwiaw redirects to front page
    """
    def get(self):
        if self.user:
            
            blogs = ndb.get_multi(self.user.blogs)
            count = 0
            for blog in blogs:
                count += 1
            self.render("front_login.html", blogs=blogs, count=count,
                        username=self.user.name, display=0, c='')
        else:
            
            blogs = ndb.gql(" SELECT * FROM Blog"
                                " ORDER BY created DESC LIMIT 10")
            
            self.render("front_page.html", blogs=blogs,
                        username='', display=0, c='')
