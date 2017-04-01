from handlers import BlogHandler
from models import Blog
from google.appengine.ext import ndb
import time


def post_exists(function):
    def wrapper(self, post_id):
        err = int(post_id.split('-')[1])
        post_id = post_id.split('-')[0]
        blogs = Blog.by_id(int(post_id))
        if blogs:
            return function(self, post_id, blogs, err)
        else:
            self.error(404)
            return
    return wrapper
         
class Editing(BlogHandler):
    """ Allows the user to edit and delete their own posts only
    """
    @post_exists
    def get(self, post_id, blogs, e):
        if self.user:
            if blogs.blog_author.get() == self.user:
                self.render('newpost.html', username=self.user.name,
                            content=blogs.content, subject=blogs.subject)
            else:
                self.redirect('/')
        else:
            self.redirect('/')

    @post_exists
    def post(self, post_id, blogs, e):
        if self.user:
            # Checking if the user is the author of the blog
            if blogs.blog_author.get() == self.user:
                subject = self.request.get("subject")
                content = self.request.get("content")

                delete = self.request.get("delete")
                reset = self.request.get("reset")
                # Deletes the post as well as comments and likes-dislike associated
                # with it
                if delete:
                    comments = ndb.get_multi(blogs.blog_comments)
                    likes = ndb.get_multi(blogs.blog_likes)
                    for l in blogs.blog_author.get().blogs:
                        if l == blogs.key:
                            blogs.blog_author.get().blogs.remove(l)
                            blogs.blog_author.get().put()
                    blogs.key.delete()
                    for comment in comments:
                        comment.key.delete()
                    for like in likes:
                        like.key.delete()
                    time.sleep(1)
                    self.redirect('/')

                # Resets any changes made to the page
                elif reset:
                    post_id += '-0'
                    self.redirect('/edit/%s' % post_id)

                # Edits the post
                else:
                    if subject and content:
                        blogs.subject = subject
                        blogs.content = content
                        blogs.put()
                        post_id += '-0'
                        self.redirect('/edit/%s' % post_id)
                    else:
                        error = "We need both Subject and Content"
                        self.render('newpost.html', username=self.user.name,
                                    error=error)
            else:
                self.redirect('/')
        else:
            self.redirect('/')
