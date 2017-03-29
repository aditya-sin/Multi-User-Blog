import os
import re
import random
import hashlib
import hmac
from string import letters
import webapp2
import jinja2
import time

from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)
# used for creating password hash
secret = 'fsdfd'


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


# Takes a value and returns a string containing the value and its hash
def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())


# Checks if the input has correct hash of the value
def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val


class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    # Sets the value of the cookie
    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    # Reads the value of the cookie if it is valid
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    # logins a user by setting the cookie
    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key.id()))

    # logouts a user by removing the value of cookie
    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    # Checks if the user is logged in and if yes sets the
    # value of self.user to the corresponding entity
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))


def make_salt(length=5):
    """ Makes salt by joining 5 random characters
    """
    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(name, pw, salt=None):
    """ Makes a hash of password using salt value
    from make_salt() if there is no salt.
    Returns a string containing salt and hash.
    """
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)


def valid_pw(name, password, h):
    """ Verifies the user inputs on login
    """
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)


class User(ndb.Model):
    """ This class makes an entity User which stores the details of user on signup
    """
    name = ndb.StringProperty(required=True)
    pw_hash = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    #userkey = ndb.KeyProperty(kind ='User', repeated = True)

    # Finds an entity of kind User using its id and returns it
    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid)

    # Finds an entity of kind User using its name and returns it
    @classmethod
    def by_name(cls, name):
        u = User.query(User.name == name).get()
        return u

    # Creates an entity of kind User and returns it
    @classmethod
    def register(cls, name, pw, email=None):
        pw_hash = make_pw_hash(name, pw)
        return User(name=name,
                    pw_hash=pw_hash,
                    email=email)

    # Validates user credentials and returns entity matching it
    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


class Blog(ndb.Model):
    """ This class creates an entity Blog which stores
    the details of blogs submitted by users.
    """
    blog_author = ndb.KeyProperty(kind='User')
    subject = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)

    def render(self, **kw):
        # Allows correct rendering of new line in the blog
        self._render_text = self.content.replace('\n', '<br>')
        count_comment = 0
        count_like = 0
        count_dislike = 0
        id_blog = self.key.id()
        comments = ndb.gql(" SELECT * From Comment"
                               " WHERE comment_blog = :num"
                               " ORDER BY comment_time DESC", num=str(id_blog))
        like = ndb.gql(" SELECT * FROM Like WHERE like_blog = :num2"
                           " AND like_dislike = 1", num2=str(id_blog))
        dislike = ndb.gql(" SELECT * FROM Like WHERE like_blog = :num2"
                              " AND like_dislike = 0", num2=str(id_blog))
        # Counting number of comments, likes and dislikes for a blog
        for comment in comments:
            count_comment += 1
        for l in like:
            count_like += 1
        for dl in dislike:
            count_dislike += 1
        id_blog = str(id_blog)+'-0'
        return render_str("post.html", p=self, comments=comments,
                          count_comment=count_comment,
                          count_like=count_like, count_dislike=count_dislike,
                          id_blog=id_blog, **kw)

    # Finds an entity of kind Blog using its id and returns it
    @classmethod
    def by_id(cls, uid):
        return Blog.get_by_id(uid)


class Comment(ndb.Model):
    comment_blog = ndb.KeyProperty()
    user_name = ndb.StringProperty(required=True)
    comment_content = ndb.StringProperty(required=True)
    comment_time = ndb.DateTimeProperty(auto_now_add=True)
    comment_id = ndb.StringProperty()

    # Finds an entity of kind Comment using its id and returns it
    @classmethod
    def by_id(cls, uid):
        return Comment.get_by_id(uid)


class Like(ndb.Model):
    like_blog = ndb.StringProperty(required=True)
    like_user = ndb.StringProperty(required=True)
    like_dislike = ndb.IntegerProperty(required=True)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')

""" Functions to validate the details of user on
signup using regular expressions.
"""


def valid_username(username):
    return username and USER_RE.match(username)


def valid_password(password):
    return password and PASS_RE.match(password)


def valid_email(email):
    return not email or EMAIL_RE.match(email)


class Signup(BlogHandler):
    """ Allows the new users to signup. If the details
    provided are not acceptable, appropriate error
    messages are given
    """
    def get(self):
        self.render("index.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        username = self.request.get('username')
        password = self.request.get('password')

        checking = self.request.get('checking')
        # checking is used to determine whether user has
        # pressed submit for login or signup. A true value
        # of checking means signup.
        if not checking:
            u = User.login(username, password)
            if u:
                self.login(u)
                self.redirect('/')
            else:
                msg = 'Invalid login'
                self.render('index.html', error=msg)

        else:
            params = dict(username=self.username,
                          email=self.email)

            # Validates details of user on signup and puts
            # appropriate error messages
            if not valid_username(self.username):
                params['err_user'] = "That's not a valid username."
                have_error = True

            if not valid_password(self.password):
                params['err_pass'] = "That wasn't a valid password."
                have_error = True
            elif self.password != self.verify:
                params['err_passmatch'] = "Your passwords didn't match."
                have_error = True

            if not valid_email(self.email):
                params['err_email'] = "That's not a valid email."
                have_error = True

            if have_error:
                self.render('index.html', **params)
            else:
                self.done()

    def done(self, *a, **kw):
        raise NotImplementedError


class Register(Signup):
    def done(self):

        # make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('index.html', err_user=msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()
            self.login(u)
            self.redirect('/')


class Logout(BlogHandler):
    """ Logouts the user and redirect to front page.
    """
    def get(self):
        self.logout()
        self.redirect('/')


class Welcome(BlogHandler):
    """ Displays form for new blog if the user is login.
    If correct values are entered, it stores the details
    of blogs in entity Blog, and redirects user to a permalink of
    that blog post.
    """
    def get(self):
        if self.user:
            self.render('newpost.html', username=self.user.name)
        else:
            self.redirect('/signup')

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")
        blog_author = self.user.key

        if subject and content:
            b = Blog(blog_author = blog_author, subject=subject, content=content)
            b.put()
            id_post = str(b.key.id())

            self.redirect("/%s" % id_post)
        else:
            error = "We need both Subject and Content"
            self.render('newpost.html', username=self.user.name, error=error)

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


class PostLink(BlogHandler):
    """ creates permalink page of the new blog post
    """
    def get(self, post_id):
        if self.user:
            blog = Blog.by_id(int(post_id))
            if not blog:
                self.error(404)
                return
            self.render("permalink.html",  blog=blog,
                        username=self.user.name, display=0, c='', err='')
        else:
            self.redirect('/')

    def post(self, post_id):
        if self.user:
            # Checking if the user has commented or not
            blog_comment = self.request.get("blog-comment")
            if blog_comment:
                blog_comment = blog_comment.replace('\n', '<br>')
                comments = Comment(comment_blog=post_id,
                                   user_name=self.user.name,
                                   comment_content=blog_comment)
                comments.put()
                comments.comment_id = str(comments.key().id())
                comments.put()
                post_id += '-0'
                self.redirect('/edit/%s' % post_id)
            else:
                post_id += '-0'
                self.redirect('/edit/%s' % post_id)


class Blogs(BlogHandler):
    """ Displays 10 most recent blogs to user whether user is login or not
    """
    def get(self):

        blogs = Blog.query().order(-Blog.created)
        #blogs = ndb.gql(" SELECT * FROM Blog"
         #                   " ORDER BY created DESC LIMIT 10")
        
        if self.user:
            #self.response.write(blogs)
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


class Posts(BlogHandler):
    """ If the user is login it displays the blog posts
    of only that particular user, otherwiaw redirects to front page
    """
    def get(self):
        if self.user:
            blogs = ndb.gql(" SELECT * FROM Blog"
                                " WHERE blog_author = :num"
                                " ORDER BY created DESC", num=self.user)
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


class Edit(BlogHandler):
    """ Allows the user to comment, edit and delete their own comments
    and like or dilike others' posts.
    """
    def get(self, post_id):
        if self.user:
            err = int(post_id.split('-')[1])
            post_id = post_id.split('-')[0]
            blogs = Blog.by_id(int(post_id))

            self.render('permalink.html', blog=blogs,
                        username=self.user.name, display=1, c='', err=err)

        else:
            post_id = post_id.split('-')[0]
            blogs = Blog.by_id(int(post_id))
            self.render('permalink_nolog.html', blog=blogs,
                        username='', display=2, c='')

    def post(self, post_id):
        if self.user:
            blog_comment = self.request.get("blog-comment")
            blog_comment = blog_comment.replace('\n', '<br>')

            like = self.request.get('like')
            dislike = self.request.get('dislike')

            comment_edit = self.request.get('edit-comment')
            comment_del = self.request.get('delete-comment')

            post_id = post_id.split('-')[0]

            # Allows the user to like or dislike the posts only once.
            # But user can dislike after liking the post and vice-versa.
            # User cannot like, dislike their own posts.
            if like or dislike:
                likes = ndb.gql(" SELECT * FROM Like"
                                    " WHERE like_blog = :num1"
                                    " AND like_user = :num2",
                                    num1=str(post_id),
                                    num2=self.user.name).get()
                b = Blog.by_id(int(post_id))
                if b.blog_author != self.user:
                    if likes:
                        if likes.like_dislike == 1:
                            if like:
                                post_id += '-1'
                                self.redirect('/edit/%s' % post_id)
                            else:
                                ndb.delete(likes)
                                post_id += '-0'
                                self.redirect('/edit/%s' % post_id)
                        else:
                            if like:
                                ndb.delete(likes)
                                post_id += '-0'
                                self.redirect('/edit/%s' % post_id)
                            else:
                                post_id += '-2'
                                self.redirect('/edit/%s' % post_id)
                    else:
                        like_blog = post_id
                        like_user = self.user.name
                        if like:
                            like_dislike = 1
                        else:
                            like_dislike = 0
                        likes = Like(like_blog=like_blog, like_user=like_user,
                                     like_dislike=like_dislike)
                        likes.put()
                        post_id += '-0'
                        self.redirect('/edit/%s' % post_id)
                else:
                    post_id += '-3'
                    self.redirect('/edit/%s' % post_id)

            # deletes the comment
            elif comment_del:
                c = ndb.gql(" SELECT * FROM Comment"
                                " WHERE comment_id = :num",
                                num=comment_del).get()
                ndb.delete(c)
                post_id += '-0'
                self.redirect('/edit/%s' % post_id)

            # edit a comment
            elif comment_edit:
                self.redirect('/edit-comment/%s' % str(comment_edit))

            # Post new comments
            else:
                if blog_comment:
                    comments = Comment(comment_blog=post_id,
                                       user_name=self.user.name,
                                       comment_content=blog_comment)
                    comments.put()
                    comments.comment_id = str(comments.key().id())
                    comments.put()
                    post_id += '-0'
                    self.redirect('/edit/%s' % post_id)
                else:
                    post_id += '-0'
                    self.redirect('/edit/%s' % post_id)

        # Users visting this page, if not logged in, have the option to login.
        else:
            username = self.request.get('username')
            password = self.request.get('password')

            u = User.login(username, password)
            if u:
                self.login(u)
                self.redirect('/')
            else:
                msg = 'Invalid login'
                post_id = post_id.split('-')[0]
                blogs = Blog.by_id(int(post_id))
                self.render('permalink_nolog.html', blog=blogs,
                            error=msg, username='', display=0, c='')


class Editing(BlogHandler):
    """ Allows the user to edit and delete their own posts only
    """
    def get(self, post_id):
        if self.user:
            post_id = post_id.split('-')[0]
            blogs = Blog.by_id(int(post_id))
            if blogs.blog_author == self.user:
                self.render('newpost.html', username=self.user.name,
                            content=blogs.content, subject=blogs.subject)
            else:
                self.redirect('/')
        else:
            self.redirect('/')

    def post(self, post_id):
        subject = self.request.get("subject")
        content = self.request.get("content")

        delete = self.request.get("delete")
        reset = self.request.get("reset")

        post_id = post_id.split('-')[0]

        # Deletes the post as well as comments and likes-dislike associated
        # with it
        if delete:
            blogs = Blog.by_id(int(post_id))
            comments = ndb.gql(" SELECT * FROM Comment"
                                   " WHERE comment_blog = :num", num=post_id)
            likes = ndb.gql(" SELECT * FROM Like"
                                " WHERE like_blog = :num", num=post_id)
            ndb.delete(blogs)
            ndb.delete(comments)
            ndb.delete(likes)
            time.sleep(1)
            self.redirect('/')

        # Resets any changes made to the page
        elif reset:
            blogs = Blog.by_id(int(post_id))
            post_id += '-0'
            self.redirect('/edit/%s' % post_id)

        # Edits the post
        else:
            if subject and content:
                blogs = Blog.by_id(int(post_id))
                blogs.subject = subject
                blogs.content = content
                blogs.put()
                post_id += '-0'
                self.redirect('/edit/%s' % post_id)
            else:
                error = "We need both Subject and Content"
                self.render('newpost.html', username=self.user.name,
                            error=error)


class Edit_Comment(BlogHandler):
    """ Allows the user to edit and delete their own comments
    """
    def get(self, comment_id):
        if self.user:
            c = Comment.by_id(int(comment_id))
            c.comment_content = c.comment_content.replace('<br>', '\n')
            c.put()
            blogs = Blog.by_id(int(c.comment_blog))
            self.render('permalink.html', blog=blogs,
                        username=self.user.name,
                        display=1, c=c, err='')

        else:
            self.redirect('/')

    def post(self, comment_id):
        c = Comment.by_id(int(comment_id))
        previous_c = c.comment_content
        post_id = c.comment_blog

        blogc = self.request.get("blog-comment")
        com_delete = self.request.get("comment-delete")
        com_reset = self.request.get("comment-reset")

        # deletes the comment
        if com_delete or not blogc:
            ndb.delete(c)
            post_id += '-0'
            self.redirect('/edit/%s' % post_id)

        # resets any changes
        elif com_reset:
            c.comment_content = previous_c.replace('\n', '<br>')
            c.put()
            post_id += '-0'
            self.redirect('/edit/%s' % post_id)

        # edits the comment
        else:
            blogc = blogc.replace('\n', '<br>')
            c.comment_content = blogc
            c.put()
            post_id += '-0'
            self.redirect('/edit/%s' % post_id)

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
