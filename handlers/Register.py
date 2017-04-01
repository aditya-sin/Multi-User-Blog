import re

from handlers import BlogHandler
from models import User

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
