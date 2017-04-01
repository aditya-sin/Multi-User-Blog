from handlers import BlogHandler
from models import Blog, Comment
from google.appengine.ext import ndb

def comment_exists(function):
    def wrapper(self, comment_id):
        comment = Comment.by_id(int(comment_id))
        if comment:
            return function(self, comment_id, comment)
        else:
            self.error(404)
        return
    return wrapper
   
class Edit_Comment(BlogHandler):
    """ Allows the user to edit and delete their own comments
    """
    @comment_exists
    def get(self, comment_id, c):
        if self.user:
            c.comment_content = c.comment_content.replace('<br>', '\n')
            c.put()
            blogs = Blog.by_id(int(c.comment_blog.id()))
            self.render('permalink.html', blog=blogs,
                        username=self.user.name,
                        display=1, c=c, err='')

        else:
            self.redirect('/')

    @comment_exists
    def post(self, comment_id, c):
        if self.user:
            # Checking if the comment is written by the user
            if c.user_name.get() == self.user:
                previous_c = c.comment_content
                post_id = str(c.comment_blog.id())

                blogc = self.request.get("blog-comment")
                com_delete = self.request.get("comment-delete")
                comment_del = self.request.get("delete-comment")
                com_reset = self.request.get("comment-reset")

                # deletes the comment
                if com_delete or comment_del:
                    for l in c.comment_blog.get().blog_comments:
                        if l == c.key:
                            c.comment_blog.get().blog_comments.remove(l)
                            c.comment_blog.get().put()
                    c.key.delete()
                    post_id += '-0'
                    self.redirect('/edit/%s' % post_id)

                # resets any changes
                elif com_reset:
                    c.comment_content = previous_c.replace('\n', '<br>')
                    c.put()
                    post_id += '-0'
                    self.redirect('/edit/%s' % post_id)

                # edits the comment
                else:
                    blogc = blogc.replace('\n', '<br>')
                    c.comment_content = blogc
                    c.put()
                    post_id += '-0'
                    self.redirect('/edit/%s' % post_id)
            else:
                self.redirect('/')
        else:
            self.redirect('/')
