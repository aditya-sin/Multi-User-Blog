import random
import hashlib
from string import letters

from google.appengine.ext import ndb

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
    blogs = ndb.KeyProperty(kind='Blog', repeated=True)
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
