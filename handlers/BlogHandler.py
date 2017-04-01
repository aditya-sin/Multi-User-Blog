import hmac
import webapp2
import jinja2
import os

from models import User

template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
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
