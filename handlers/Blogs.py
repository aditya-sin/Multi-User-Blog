from handlers import BlogHandler
from models import Blog, User
from google.appengine.ext import ndb


class Blogs(BlogHandler):
    """ Displays 10 most recent blogs to user whether user is login or not
    """
    def get(self):
        blogs = Blog.query().order(-Blog.created)
        if self.user:
            self.render("front_login.html",  blogs=blogs, count=1,
                        username=self.user.name, display=0, c='')
        else:
            self.render("front_page.html", blogs=blogs,
                        display=0, username='', c='')

    def post(self):
        # logins a user if the details are valid
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/')
        else:
            msg = 'Invalid login'
            blogs = ndb.gql(" SELECT * FROM Blog"
                                " ORDER BY created DESC LIMIT 10")
            self.render('front_page.html', blogs=blogs,
                        error=msg, username='', display=0, c='')
