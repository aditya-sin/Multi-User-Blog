import re
import hmac
import webapp2

from google.appengine.ext import ndb

from models import Like, Comment, Blog, User
from handlers import BlogHandler, Register, Logout, Welcome, PostLink
from handlers import Blogs, Posts, Edit, Editing, Edit_Comment

from google.appengine.api import app_identity
server_url = app_identity.get_default_version_hostname()


""" Some variable are used to control the behaviour of app as per the need.
display=1 : Shows comment-box, previous comments, edit option on comment and
like/dislike buttons.
display=2 : Shows previous comments only. This is for users who are not
logged in
display=0 : Show none of the above. This is used at main page where only
blog-posts are shown.
c: tells whether the user wants to edit his previous comment.
err: Different values are used to display errors related to like/dislike,
deleting posts and deleting comments.
"""

app = webapp2.WSGIApplication([('/', Blogs),
                               ('/signup', Register),
                               ('/welcome', Welcome),
                               ('/logout', Logout),
                               ('/([0-9]+)', PostLink),
                               ('/posts', Posts),
                               ('/edit/([0-9].+)', Edit),
                               ('/editing/([0-9].+)', Editing),
                               ('/edit-comment/([0-9].+)', Edit_Comment)
                               ],
                              debug=True)
