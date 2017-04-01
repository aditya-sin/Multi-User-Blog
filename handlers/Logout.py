from handlers import BlogHandler


class Logout(BlogHandler):
    """ Logouts the user and redirect to front page.
    """
    def get(self):
        self.logout()
        self.redirect('/')
