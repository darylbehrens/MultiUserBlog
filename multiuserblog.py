import os
import webapp2
import jinja2
import re
import string
from google.appengine.ext import db
from modules.models import *
from modules.hashing import *
from modules.handler import *
from modules.authetication import *


class WelcomPage(Handler):

    def get(self):
        user_id = self.verify_user()
        if user_id:
            login_name = User.get_name_by_id(int(user_id))
            self.render("welcome.html", login_name=login_name)
        else:
            self.redirect('/signup?error_message=You must '
                'be logged in to view your home page')

# List of blogs
class MainBlogPage(Handler):
    def render_index(self):
        valid_user = self.verify_user()
        if valid_user:
            login_name=User.get_name_by_id(int(valid_user))
        else:
            login_name = "guest"
        user_id = ""

        # Check if another user was specified, if so send to that users
        # blog page
        user = self.request.get("username")
        if user:
            user_id = User.get_id_by_name(user)
        else:
            user_id = valid_user

        if user_id:
            posts = db.GqlQuery(
                "SELECT * FROM Blog WHERE owner = %s" % user_id)

            # sort by date, since I was getting an index error
            display_posts = []
            for post in posts:
                display_posts.append(post)
            print len(display_posts)
            display_posts.sort(key=lambda x: x.created, reverse=True)
            self.render("blog.html", posts=display_posts,
                            login_name=login_name)
        else:
            self.redirect('/users?errormessage=You must be '
                'logged in to view your own blog')

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
            login_name = User.get_name_by_id(int(valid_user))
            self.render("newpost.html", login_name=login_name,
                        form_type=form_type, error_message=error_message)
        else:
            self.redirect('/users?errormessage=You must be '
                'logged in to post')

    def post(self):
        valid_user = self.verify_user()
        if valid_user:
            subject = self.request.get("subject")
            content = self.request.get("content")
            
            if subject and content:
                post = Blog(subject=subject, content=content,
                                owner=int(valid_user))
                post.put()
                id = post.key().id()
                self.redirect("/blog/%d" % id)
            else:
                error_message = "Must have subject and content"
                self.redirect("/blog/newpost?post_id=%s&error_message=%s" %
                              (post_id, error_message))
        else:
            self.redirect('/users?errormessage=You must be '
                'logged in to post')

# This handles the individual post page
# If the person viewing the page is the post owner, is_owner gets set to true
# If the person viewing the page is not the post owner, they can
# upvote/downvote
class PostPage(Handler):

    def get(self, postId):
        valid_user = self.verify_user()
        is_owner = True
        error_message = self.request.get("errormessage")
        post = Blog.get_by_id(int(postId))
        
        # css for making thumbs up or down bold
        upvote = "normal"
        downvote = "normal"

        #user is logged in
        if valid_user:
            login_name = User.get_name_by_id(int(valid_user))
            # get higlights for upvote or downvote
            # button depending on vote status
            vote = db.GqlQuery(
                "SELECT * FROM Votes "
                "WHERE post_id = %d and votedby = %d" 
                % (int(postId), int(valid_user))).get()

            if vote:
                if vote.votetype == 1:
                    upvote = "bold"
                elif vote.votetype == -1:
                    downvote = "bold"
            # if owner of post is not current user
            if str(post.owner) != str(valid_user):
                is_owner = False
        #guest User
        else:            
            is_owner = False
            login_name = "guest"

        # get comments
        comments = Comment.all().filter("post_id =", int(postId))
        display_comments = []
        for comment in comments:
            display_comments.append(comment)
        display_comments.sort(key=lambda x: x.created, reverse = True)
        self.render("blog.html", posts=[post],
                    login_name=login_name,
                    is_owner=is_owner, is_edit=True,
                    comments=comments, errormessage=error_message,
                    downvote=downvote, upvote=upvote)

    # save Comment
    def post(self, post_id):
        valid_user = self.verify_user()
        if valid_user:
            comment_text = self.request.get("comment")
            comment = Comment(post_id=int(post_id), owner=User.get_name_by_id(
                int(valid_user)), text=comment_text)
            comment.put()
            self.redirect("/blog/%d" % int(post_id))
        else:
            self.redirect('/blog/%d?errormessage=You must be '
                'logged in to comment' % int(post_id))

# Shows a list of users to browse blogs
class UsersPage(Handler):

    def get(self):
        valid_user = self.verify_user()
        errormessage = self.request.get("errormessage");
        if valid_user:
            username = User.get_name_by_id(int(valid_user))
        else:
            username = "guest"
        users = User.all().filter("username !=", username)
        display_users = []
        for user in users:
            display_users.append(user)
        for i in xrange(len(display_users)):
            posts = Blog.all().filter(
                "owner =", int(display_users[i].key().id()))
            display_users[i].score = sum(post.score for post in posts)
        display_users.sort(key=lambda x: x.score, reverse=True)
        self.render("users.html", users=display_users, login_name=username,
            errormessage = errormessage)
        

# Deletes Blog Post if owned by current user
class DeletePage(Handler):

    def post(self, postId):
        valid_user = self.verify_user()
        if valid_user:
            blog = Blog.get_by_id(int(postId))
            if blog:
                # Make Sure only owner can delete post
                if (str(valid_user) == str(blog.owner)):
                    blog.delete()
                    self.redirect("/blog/%s" % postId)
                else:
                    self.redirect(
                        ("/blog/%s?errormessage=You can "
                         "not delete another users posts") % postId)
                self.redirect('/blog')
            else:
                self.redirect('/blog/welcome')
        else:
            self.redirect('/blog/%d?errormessage=You must be '
                'logged in to delete a post' % int(postId))

# Edits Blog Post
class EditPage(Handler):

    def get(self, postId):
        valid_user = self.verify_user()
        if valid_user:
            subject = ""
            content = ""
            error_message = self.request.get("error_message")
            # Check if a post Id was passed for edit
            post = Blog.get_by_id(int(postId))
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
        else:
            self.redirect('/blog/%d?errormessage=You must be '
                'logged in to edit a post' % int(postId))
        login_name = User.get_name_by_id(int(valid_user))
        self.render("newpost.html", login_name=login_name,
                        error_message=error_message,
                        subject = subject, content = content,
                        form_type = form_type,
                        action = "/blog/edit/%d" % int(postId))


    def post(self, post_id):
        valid_user = self.verify_user()
        if valid_user:
            subject = self.request.get("subject")
            content = self.request.get("content")
            if post_id:
                post = Blog.get_by_id(int(post_id))
                if post:
                    # check if person trying to edit is owner of post
                    if str(valid_user) == str(post.owner):
                        post.subject = subject
                        post.content = content
                        post.put()
                    else:
                        # Something Fishy is going on, redirect
                        self.redirect('/blog/welcome')
                else:
                    # Something Fishy is going on, redirect
                    self.redirect('/blog/welcome')
        else:
            self.redirect('/blog/%d?errormessage=You must be'
                ' logged in to edit post' % int(post_id))
        self.redirect("/blog/%d" % int(post_id))

# Checks if user already upvoted, if so gives warning, if not allows
class ScoreUpPage(Handler):

    def post(self, postId):
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
            self.redirect('/blog/%d?errormessage=You must be '
                'logged in to vote' % int(postId))

# Checks if user already downvoted, if so gives warning, if not allows
class ScoreDownPage(Handler):

    def post(self, postId):
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
            self.redirect('/blog/%d?errormessage=You must be '
                'logged in to vote' % int(postId))

# Deletes Comment if owned by current user
class DeleteCommentPage(Handler):

    def post(self):
        post_id = self.request.get("post_id")
        comment_id = self.request.get("comment_id")
        valid_user = self.verify_user()
        if valid_user:
            comment = Comment.get_by_id(int(comment_id))
            if comment:
                # Make Sure only owner can delete post
                if (str(User.get_name_by_id(int(valid_user))) == str(comment.owner)):
                    comment.delete()
                    self.redirect("/blog/%d" % int(post_id))
                else:
                    self.redirect(
                        ("/blog/%s?errormessage=You can "
                         "not delete another users Comment") % post_id)
            else:
                self.redirect('/blog/welcome')
        else:
            self.redirect('/blog/%d?errormessage=You must be '
                'logged in to delete comment' % int(post_id))

class EditCommentPage(Handler):
    def post(self, commentId):
        valid_user = self.verify_user()
        if valid_user:
            comment = Comment.get_by_id(int(commentId))
            if comment:
                # Make Sure only owner can delete post
                if (str(User.get_name_by_id(int(valid_user))) == str(comment.owner)):
                    post_id = self.request.get("postid")
                    comment_text = self.request.get("mycomment")
                    comment.text = comment_text
                    comment.put()
                    self.redirect("/blog/%d" % int(post_id))
                else:
                    self.redirect(
                        ("/blog/%s?errormessage=You can "
                         "not edit another users Comment") % post_id)
            else:
                self.redirect('/blog/welcome')
        else:
            self.redirect('/blog/%d?errormessage=You must be '
                'logged in to edit a comment' % int(post_id))

app = webapp2.WSGIApplication([
    ('/', LoginPage),
    ('/signup', SignupPage), ('/blog/welcome', WelcomPage),
    ('/login', LoginPage), ('/logoff', LogoffPage),
    ('/blog', MainBlogPage), ('/blog/newpost', NewPost),
    ('/blog/([0-9]+)', PostPage), ('/users', UsersPage),
    ('/blog/delete/([0-9]+)', DeletePage),
    ('/blog/edit/([0-9]+)', EditPage),
    ('/blog/thumbsup/([0-9]+)', ScoreUpPage),
    ('/blog/thumbsdown/([0-9]+)', ScoreDownPage),
    ('/blog/deletecomment', DeleteCommentPage),
    ('/blog/editcomment/([0-9]+)', EditCommentPage)
    ], debug=True)
