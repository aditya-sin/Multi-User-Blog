from handlers import BlogHandler
from models import User, Blog


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
        if self.user:
            subject = self.request.get("subject")
            content = self.request.get("content")
            blog_author = self.user.key
            

            if subject and content:
                b = Blog(blog_author = blog_author, subject=subject, content=content)
                b.put()
                self.user.blogs = (b.key,)
                self.user.put()
                id_post = str(b.key.id())

                self.redirect("/%s" % id_post)
            else:
                error = "We need both Subject and Content"
                self.render('newpost.html', username=self.user.name, error=error)
        else:
            self.redirect('/')
