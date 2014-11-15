import logging
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

import random
import time

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

excerpt_array = [Excerpt('audio/CakeSSLJ.mp3'),
    Excerpt('audio/SmithsHSIN.mp3'),
    Excerpt('audio/ArcticDIWK.mp3')]

excerpt_array[0].addFollowing([excerpt_array[2]])
excerpt_array[1].addFollowing([excerpt_array[2]])
excerpt_array[2].addFollowing([excerpt_array[1]])

START_OPTIONS = [excerpt_array[0]]

current_excerpt = 'start'

def audioKey(audio_url):
    """Constructs a Datastore key for the url for an audio file, audio_url."""
    return ndb.Key('AudioUrl', audio_url)

def aggregateKey():
    """Constructs a Datastore key for the aggregated excerpt data"""
    return ndb.Key('AggKey', '1')

class Session(ndb.Model):
    """Models an individual listening session entry."""
    listener = ndb.UserProperty()
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    laugh_array = ndb.TextProperty()

class Aggregate(ndb.Model):
    """Models aggregated data over an audio excerpt."""
    audio_url = ndb.StringProperty()
    total_laughs = ndb.TextProperty()
    total_listens = ndb.IntegerProperty(indexed=False)


class MainPage(webapp2.RequestHandler):

    def _loadPage(self):

        global current_excerpt
        if current_excerpt == 'start':
            current_excerpt = START_OPTIONS[random.randint(0, len(START_OPTIONS) - 1)]
        else:
            following_excerpts = current_excerpt.getFollowing()
            current_excerpt = following_excerpts[random.randint(0, len(following_excerpts) - 1)]

        aggregate = Aggregate.get_by_id(current_excerpt.getFileURL(), parent = aggregateKey())
        logging.debug(str(aggregate))

        if aggregate is None or aggregate.total_listens is None:
            total_listens = 0
        else:
            total_listens = aggregate.total_listens
        if aggregate is None or aggregate.total_laughs is None:
            total_laughs = ''
        else:
            total_laughs = aggregate.total_laughs

        template_values = {
            'audio_url': current_excerpt.getFileURL(),
            'total_laughs': total_laughs,
            'total_listens': total_listens,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

    def get(self):

        global current_excerpt
        current_excerpt = 'start'
        self._loadPage()

    def post(self):

        session = Session(parent = audioKey(self.request.get('audio_url')))
        session.laugh_array = self.request.get('laugh_array')
        if users.get_current_user():
            session.listener = users.get_current_user()
        key = session.put()
        logging.info('Added session: ' + str(key))
        self._loadPage()


class Aggregator(webapp2.RequestHandler):

    def get(self):
       
        global excerpt_array

        start = time.time()
        session_count = 0

        for excerpt in excerpt_array:
            excerpt_query = Session.query(ancestor = audioKey(excerpt.getFileURL()))
            total_laughs = []
            total_listens = 0
            for session in excerpt_query:
                if session.laugh_array is not None:
                    laugh_str = session.laugh_array.split(',')
                    laugh_array = [int(laugh) for laugh in laugh_str]
                else:
                    laugh_array = []
                if len(laugh_array) > len(total_laughs):
                    total_laughs += ([0]*(len(laugh_array) - len(total_laughs)))
                for i in range(len(laugh_array)):
                    total_laughs[i] += laugh_array[i]
                total_listens += 1
                session_count += 1
            aggregate = Aggregate(parent = aggregateKey(), id = excerpt.getFileURL())
            aggregate.audio_url = excerpt.getFileURL()
            aggregate.total_laughs = str(total_laughs).strip('[]')
            aggregate.total_listens = total_listens
            key = aggregate.put()
            logging.debug('Added aggregation: ' + str(key))
        end = time.time()

        template_values = {
            'elapsed_time': end - start,
            'excerpt_num': len(excerpt_array),
            'session_count': session_count,
        }
        template = JINJA_ENVIRONMENT.get_template('aggregate.html')
        self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/yo', MainPage),
    ('/aggregate', Aggregator),
], debug=True)