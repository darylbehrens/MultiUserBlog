import hashing
from handler import *
from models import *
import re
import string

class SignupPage(Handler):

    def get(self):
        valid_user = self.verify_user()
        if not valid_user:
            username = self.request.get("username")
            error_message = self.request.get("error_message")
            self.render("signup.html", username=username,
                error_message = error_message)
        else:
            self.redirect('/blog/welcome')

    def post(self):
        valid_user = self.verify_user()
        if not valid_user:
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
                    if username.lower() == "guest":
                        usernameError = "Cant have username guest"

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
        else:
            self.redirect('/blog/welcome')




class LoginPage(Handler):

    def get(self):
        valid_user = self.verify_user()
        if not valid_user:
            username = self.request.get("username")
            self.render("login.html", username=username)
        else:
            self.redirect('/blog/welcome')

    def post(self):
        valid_user = self.verify_user()
        if not valid_user:
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
        else:
            self.redirect('/blog/welcome')

class LogoffPage(Handler):

    def get(self):
        self.clear_cookie("user_id")
        self.redirect('/login')