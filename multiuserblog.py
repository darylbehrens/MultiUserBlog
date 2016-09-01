import os
import webapp2
import jinja2
import re
import hmac
import random
import string
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_evn = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

SECRET = "isdfadf"


# Cookie Hashing

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


class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    salt = db.StringProperty(required=True)
    email = db.StringProperty
    score = 0

    @classmethod
    def get_name_by_id(cls, uid):
        user = User.get_by_id(uid)
        if user:
            return user.username

    @classmethod
    def get_id_by_name(cls, name):
        user = User.all().filter('username =', name).get()
        if user:
            return user.key().id()


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


class SignupPage(Handler):

    def get(self):
        username = self.request.get("username")
        self.render("signup.html", username=username)

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")
        valid = True
        usernameError = ""
        passwordError = ""
        verifyError = ""
        emailError = ""

        if username:
            user_re = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
            if not user_re.match(username):
                valid = False
                usernameError = "Invalid User Name"
        else:
            usernameError = "Must Enter A User Name"
            valid = False

        if password:
            password_re = re.compile(r"^.{3,20}$")
            if not password_re.match(password):
                passwordError = "Must Enter A Valid Password"
                valid = False
            elif password != verify:
                verifyError = "Passwords Dont Match"
                valid = False
        else:
            passwordError = "Must Enter A Password"
            valid = False

        if email:
            email_re = re.compile(r"^[\S]+@[\S]+.[\S]+$")
            if not email_re.match(email):
                emailError = "Must Enter A Vaild Email"
                valid = False

        # Verify user name is not taken
        user = User.all().filter("username =", username).get()
        if valid == True and user:
            usernameError = "This Name Is Already Taken"
            valid = False

        if not valid:
            self.render("signup.html",
                        username=username,
                        password=password,
                        verify=verify,
                        email=email,
                        usernameError=usernameError,
                        passwordError=passwordError,
                        verifyError=verifyError,
                        emailError=emailError)
        else:
            salt = get_salt()
            full_hash = make_secure_val(password, salt)
            myhash = full_hash.split('|')[1]
            user = User(username=username, password=myhash,
                        salt=salt, email=email)
            user.put()
            self.set_cookie_value('user_id', user.key().id())
            self.redirect('/blog/welcome')


class WelcomPage(Handler):

    def get(self):
        user_id = self.verify_user()
        if user_id:
            login_name = User.get_name_by_id(int(user_id))
            self.render("welcome.html", login_name=login_name)
        else:
            self.redirect('/signup')


class LoginPage(Handler):

    def get(self):
        username = self.request.get("username")
        self.render("login.html", username=username)

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        q = User.all()
        q.filter("username ==", username)
        user = None
        for p in q.run(limit=5):
            user = p
        if user:
            full_hash = make_secure_val(password, user.salt)
            if full_hash.split('|')[1] == user.password:
                self.set_cookie_value('user_id', user.key().id())
                self.redirect('/blog/welcome')
        error_message = "Invalid Login"
        self.render("login.html", username=username,
                    error_message=error_message)


class LogoffPage(Handler):

    def get(self):
        self.clear_cookie("user_id")
        self.redirect('/login')


class Blog(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    owner = db.IntegerProperty(required=True)
    score = db.IntegerProperty(default=0)

# List of blogs
class MainBlogPage(Handler):
    def render_index(self):
        valid_user = self.verify_user()
        user_id = ""
        if valid_user:
            # Check if another user was specified, if so send to that users
            # blog page
            user = self.request.get("username")
            if user:
                user_id = User.get_id_by_name(user)
            else:
                user_id = valid_user
            posts = db.GqlQuery(
                ("SELECT * FROM Blog WHERE "
                 "owner = %s ORDER BY created DESC") % user_id)
            self.render("blog.html", posts=posts,
                        login_name=User.get_name_by_id(int(valid_user)))
        else:
            self.redirect('/signup')

    def get(self):
        self.render_index()

# Handles creating new posts or editing old posts
class NewPost(Handler):
    def get(self):
        valid_user = self.verify_user()
        error_message = self.request.get("error_message")
        if valid_user:
            subject = ""
            content = ""
            # Header Defaults To 'New Post'
            form_type = "New Post"
            post_id = self.request.get("post_id")

            # Check if a post Id was passed for edit
            if post_id and post_id != '/':
                post = Blog.get_by_id(int(post_id))
                if post:
                    # check if person trying to edit is owner of post
                    if str(valid_user) == str(post.owner):
                        # To Set Header to Edit Post
                        form_type = "Edit Post"
                        subject = post.subject
                        content = post.content
                    else:
                        # User is Trying To Edit someone Elses post
                        self.redirect(
                            ('/blog/%s?errormessage=You can not',
                             'edit another users posts') % post_id)
                else:
                    # Something Fishy is going on, redirect
                    self.redirect('/blog/welcome')

            login_name = User.get_name_by_id(int(valid_user))
            self.render("newpost.html", login_name=login_name,
                        post_id=post_id, subject=subject,
                        content=content, form_type=form_type,
                        error_message=error_message)
        else:
            self.redirect('/signup')

    def post(self):
        valid_user = self.verify_user()
        if valid_user:
            subject = self.request.get("subject")
            content = self.request.get("content")
            post_id = self.request.get("post_id")
            post = None
            if subject and content:
                if post_id and post_id != "/":
                    post = Blog.get_by_id(int(post_id))
                    if post:
                        # check if person trying to edit is owner of post
                        if str(valid_user) == str(post.owner):
                            print subject
                            post.subject = subject
                            post.content = content
                        else:
                            # Something Fishy is going on, redirect
                            self.redirect('/blog/welcome')
                    else:
                        # Something Fishy is going on, redirect
                        self.redirect('/blog/welcome')
                else:
                    post = Blog(subject=subject, content=content,
                                owner=int(valid_user))
                post.put()
                id = post.key().id()
                print id
                self.redirect("/blog/%d" % id)
            else:
                error_message = "Must have subject and content"
                self.redirect("/blog/newpost?post_id=%s&error_message=%s" %
                              (post_id, error_message))
        else:
            self.redirect('/signup')

# This handles the individual post page
# If the person viewing the page is the post owner, is_owner gets set to true
# If the person viewing the page is not the post owner, they can
# upvote/downvote
class PostPage(Handler):

    def get(self, postId):
        valid_user = self.verify_user()
        is_owner = True
        error_message = self.request.get("errormessage")
        if valid_user:

            # get higlights for upvote or downvote
            # button depending on vote status
            vote = db.GqlQuery(
                "SELECT * FROM Votes "
                "WHERE post_id = %d and votedby = %d" 
                % (int(postId), int(valid_user))).get()

            upvote = "normal"
            downvote = "normal"
            if vote:
                if vote.votetype == 1:
                    upvote = "bold"
                elif vote.votetype == -1:
                    downvote = "bold"
            post = Blog.get_by_id(int(postId))

            # if owner of post is not current user
            if str(post.owner) != str(valid_user):
                is_owner = False

            # get comments
            comments = Comment.all().filter("post_id =", int(postId))
            login_name = User.get_name_by_id(int(valid_user))
            self.render("blog.html", posts=[post],
                        login_name=login_name,
                        is_owner=is_owner, is_edit=True,
                        comments=comments, errormessage=error_message,
                        downvote=downvote, upvote=upvote)
        else:
            self.redirect('/signup')

    def post(self, post_id):
        valid_user = self.verify_user()
        if valid_user:
            comment_text = self.request.get("comment")
            comment = Comment(post_id=int(post_id), owner=User.get_name_by_id(
                int(valid_user)), text=comment_text)
            comment.put()
            self.redirect("/blog/%d" % int(post_id))
        else:
            self.redirect('/signup')

# Shows a list of users to browse blogs
class UsersPage(Handler):

    def get(self):
        valid_user = self.verify_user()
        if valid_user:
            username = User.get_name_by_id(int(valid_user))
            users = User.all().filter("username !=", username)
            display_users = []
            for user in users:
                display_users.append(user)
            for i in xrange(len(display_users)):
                posts = Blog.all().filter(
                    "owner =", int(display_users[i].key().id()))
                display_users[i].score = sum(post.score for post in posts)
            display_users.sort(key=lambda x: x.score, reverse=True)
            self.render("users.html", users=display_users, login_name=username)
        else:
            self.redirect('/signup')

# Deletes Blog Post if owned by current user
class DeletePage(Handler):

    def get(self, postId):
        valid_user = self.verify_user()
        if valid_user:
            blog = Blog.get_by_id(int(postId))
            if blog:
                # Make Sure only owner can delete post
                if (str(valid_user) == str(blog.owner)):
                    blog.delete()
                else:
                    self.redirect(
                        ("/blog/%s?errormessage=You can "
                         "not delete another users posts") % postId)
                self.redirect('/blog')
            else:
                self.redirect('/blog/welcome')
        else:
            self.redirect('/signup')

# Edits Blog Post
class EditPage(Handler):

    def get(self, postId):
        self.redirect('/blog/newpost?post_id=%d' % int(postId))

# Checks if user already upvoted, if so gives warning, if not allows
class ScoreUpPage(Handler):

    def get(self, postId):
        valid_user = self.verify_user()
        if valid_user:
            vote = db.GqlQuery(
                ("SELECT * FROM Votes "
                 "WHERE post_id = %d and votedby = %d") %
                (int(postId), int(valid_user))).get()
            if vote:
                if vote.votetype == 1:
                    self.redirect(
                        ("/blog/%d?errormessage="
                         "You have already upvoted this post") % int(postId))
                else:
                    vote.votetype = 1
                    vote.put()
                    blog = Blog.get_by_id(int(postId))
                    blog.score = blog.score + 2
                    blog.put()
                    self.redirect("/blog/%d" % int(postId))
            else:
                vote = Votes(post_id=int(postId),
                             votedby=int(valid_user), votetype=1)
                vote.put()
                blog = Blog.get_by_id(int(postId))
                blog.score = blog.score + 1
                blog.put()
                self.redirect("/blog/%d" % int(postId))
        else:
            self.redirect('/signup')

# Checks if user already downvoted, if so gives warning, if not allows
class ScoreDownPage(Handler):

    def get(self, postId):
        valid_user = self.verify_user()
        if valid_user:
            vote = db.GqlQuery(
                ("SELECT * FROM Votes "
                 "WHERE post_id = %d and votedby = %d")
                % (int(postId), int(valid_user))).get()
            if vote:
                if vote.votetype == -1:
                    self.redirect(
                        ("/blog/%d?errormessage="
                         "You have already downvoted this post") % int(postId))
                else:
                    vote.votetype = -1
                    vote.put()
                    blog = Blog.get_by_id(int(postId))
                    blog.score = blog.score - 2
                    blog.put()
                    self.redirect("/blog/%d" % int(postId))
            else:
                vote = Votes(post_id=int(postId),
                             votedby=int(valid_user), votetype=-1)
                vote.put()
                blog = Blog.get_by_id(int(postId))
                blog.score = blog.score - 1
                blog.put()
                self.redirect("/blog/%d" % int(postId))
        else:
            self.redirect('/signup')

# Comments Entity
class Comment(db.Model):
    post_id = db.IntegerProperty(required=True)
    owner = db.StringProperty(required=True)
    text = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

# Votes Entity
class Votes(db.Model):
    post_id = db.IntegerProperty(required=True)
    votedby = db.IntegerProperty(required=True)
    votetype = db.IntegerProperty(default=0)

app = webapp2.WSGIApplication([
    ('/signup', SignupPage), ('/blog/welcome', WelcomPage),
    ('/login', LoginPage), ('/logoff', LogoffPage),
    ('/blog', MainBlogPage), ('/blog/newpost', NewPost),
    ('/blog/([0-9]+)', PostPage), ('/users', UsersPage),
    ('/blog/delete/([0-9]+)', DeletePage),
    ('/blog/edit/([0-9]+)', EditPage),
    ('/blog/thumbsup/([0-9]+)', ScoreUpPage),
    ('/blog/thumbsdown/([0-9]+)', ScoreDownPage)], debug=True)
