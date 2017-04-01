from handlers import BlogHandler
from models import Blog,Comment, Like
from google.appengine.ext import ndb

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

class Edit(BlogHandler):
    """ Allows the user to comment, edit and delete their own comments
    and like or dilike others' posts.
    """
    @post_exists
    def get(self, post_id, blogs, err):
        if self.user:
            self.render('permalink.html', blog=blogs,
                        username=self.user.name, display=1, c='', err=err)
        else:
            self.render('permalink_nolog.html', blog=blogs,
                        username='', display=2, c='')

    @post_exists
    def post(self, post_id, b, err):
        if self.user:
            blog_comment = self.request.get("blog-comment")
            blog_comment = blog_comment.replace('\n', '<br>')

            like = self.request.get('like')
            dislike = self.request.get('dislike')

            comment_edit = self.request.get('edit-comment')
            #comment_del = self.request.get('delete-comment')

            # Allows the user to like or dislike the posts only once.
            # But user can dislike after liking the post and vice-versa.
            # User cannot like, dislike their own posts.
            if like or dislike:
                likes = ndb.gql(" SELECT * FROM Like"
                                    " WHERE like_blog = :num1"
                                    " AND like_user = :num2",
                                    num1=b.key,
                                    num2=self.user.key).get()
                if b.blog_author.get().name != self.user.name:
                    if likes:
                        if likes.like_dislike == 1:
                            if like:
                                post_id += '-1'
                                self.redirect('/edit/%s' % post_id)
                            else:
                                for l in b.blog_likes:
                                    if l == likes.key:
                                        b.blog_likes.remove(l)
                                        b.put()      
                                likes.key.delete()
                                post_id += '-0'
                                self.redirect('/edit/%s' % post_id)
                        else:
                            if like:
                                for l in b.blog_likes:
                                    if l == likes.key:
                                        b.blog_likes.remove(l)
                                        b.put()
                                likes.key.delete()
                                post_id += '-0'
                                self.redirect('/edit/%s' % post_id)
                            else:
                                post_id += '-2'
                                self.redirect('/edit/%s' % post_id)
                    else:
                        like_blog = b.key
                        like_user = self.user.key
                        if like:
                            like_dislike = 1
                        else:
                            like_dislike = 0
                        likes = Like(like_blog=like_blog, like_user=like_user,
                                     like_dislike=like_dislike)
                        likes.put()
                        b.blog_likes.append(likes.key)
                        b.put()
                        post_id += '-0'
                        self.redirect('/edit/%s' % post_id)
                else:
                    post_id += '-3'
                    self.redirect('/edit/%s' % post_id)

            # edit a comment
            elif comment_edit:
                self.redirect('/edit-comment/%s' % str(comment_edit))

            # Post new comments
            else:
                if blog_comment:
                    comments = Comment(comment_blog=b.key,
                                       user_name=self.user.key,
                                       comment_content=blog_comment)
                    comments.put()
                    comments.comment_id = str(comments.key.id())
                    comments.put()
                    b.blog_comments.append(comments.key)
                    b.put()
                    post_id += '-0'
                    self.redirect('/edit/%s' % post_id)
                else:
                    post_id += '-0'
                    self.redirect('/edit/%s' % post_id)

        # Users visting this page, if not logged in, have the option to login.
        else:
            self.redirect('/')
