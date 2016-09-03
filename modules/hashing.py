import hmac
import random
import string

# Cookie Hashing
SECRET = "isdfadf"


def hash_cookie(val):
    return hmac.new(SECRET, str(val)).hexdigest()


def make_secure_cookie(val):
    return "%s|%s" % (val, hash_cookie(val))


def check_secure_cookie(val, hash):
    if hash == make_secure_cookie(val):
        return True


def get_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))


def hash_str(str, salt=None):
    return hmac.new(SECRET, str + salt).hexdigest()


def make_secure_val(str, salt=None):
    if not salt:
        salt = get_salt()
    return "%s|%s|%s" % (str, hash_str(str, salt), salt)


def check_secure_val(str, h):
    salt = h.split('|')[2]
    if (h == make_secure_val(str, salt)):
        return True