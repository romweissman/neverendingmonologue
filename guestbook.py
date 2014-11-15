import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

import random

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Excerpt:

    def __init__(self, file_url):
        self.file_url = file_url
        self.following = []

    def addFollowing(self, following_excerpts):
        self.following = self.following + following_excerpts

    def removeAllFollowing(self):
        self.following = []

    def getFileURL(self):
        return self.file_url

    def getFollowing(self):
        return self.following

CAKESSLJ = Excerpt('audio/CakeSSLJ.mp3')
SMITHSHSIN = Excerpt('audio/SmithsHSIN.mp3')
ARCTICDIWK = Excerpt('audio/ArcticDIWK.mp3')
CAKESSLJ.addFollowing([ARCTICDIWK])
SMITHSHSIN.addFollowing([ARCTICDIWK])
ARCTICDIWK.addFollowing([SMITHSHSIN])


START_OPTIONS = [CAKESSLJ]

current_excerpt = 'start'

# We set a parent key on the 'Greetings' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

class MainPage(webapp2.RequestHandler):

    def _loadPage(self):
        
        global current_excerpt
        if current_excerpt == 'start':
            current_excerpt = START_OPTIONS[random.randint(0, len(START_OPTIONS) - 1)]
        else:
            following_excerpts = current_excerpt.getFollowing()
            current_excerpt = following_excerpts[random.randint(0, len(following_excerpts) - 1)]

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'audio_url': current_excerpt.getFileURL(),
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


    def get(self):

        global current_excerpt
        current_excerpt = 'start'
        self._loadPage()

    def post(self):

        self._loadPage()

        


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/yo', MainPage),
], debug=True)