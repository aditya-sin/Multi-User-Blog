from handlers import BlogHandler
from models import Blog


class PostLink(BlogHandler):
    """ creates permalink page of the new blog post
    """
    def get(self, post_id):
        if self.user:
            blog = Blog.by_id(int(post_id))
            if not blog:
                self.error(404)
                return
            self.render("permalink.html",  blog=blog,
                        username=self.user.name, display=1, c='', err='')
        else:
            self.redirect('/')
