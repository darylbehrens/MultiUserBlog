import webapp2
import os
from hashing import *
import jinja2


template_dir = os.path.join(os.path.dirname(__file__), '../templates')
jinja_evn = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_evn.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def get_cookie(self, name):
        user_cookie = self.request.cookies.get(name)
        if user_cookie:
            return user_cookie

    def get_cookie_value(self, cookie_string):
        value = cookie_string.split('|')[0]
        if check_secure_cookie(value, cookie_string) == True:
            return value

    def set_cookie_value(self, name, value):
        self.response.headers.add_header(
            'Set-Cookie',
            name + '=' + str(make_secure_cookie(value)) +
            '; Path=/')

    def clear_cookie(self, name):
        self.response.headers.add_header('Set-Cookie', name + '=; Path=/')

    def verify_user(self):
        user_cookie = self.get_cookie("user_id")
        if user_cookie:
            user_id = self.get_cookie_value(user_cookie)
            if user_id:
                if check_secure_cookie(user_id, user_cookie) == True:
                    return user_id
