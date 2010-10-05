#!/usr/bin/env python
# coding=utf-8

import os
import time
import datetime
import wsgiref.handlers

from v2ex.picky.ext import twitter
from v2ex.picky import Datum

from version import *

from v2ex.picky.security import CheckAuth, DoAuth

from v2ex.picky.ext.sessions import Session

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import users

site_domain = Datum.get('site_domain')
site_name = Datum.get('site_name')
site_author = Datum.get('site_author')
site_slogan = Datum.get('site_slogan')
site_analytics = Datum.get('site_analytics')

user = users.get_current_user()

MODE_TWITTER = True

class TwitterHomeHandler(webapp.RequestHandler):
  def get(self):
    self.session = Session()
    if CheckAuth(self) is False:
      return DoAuth(self, '/twitter')
    template_values = {}
    twitter_account = Datum.get('twitter_account')
    twitter_password = Datum.get('twitter_password')
    api = twitter.Api(username=twitter_account, password=twitter_password)
    limit = api.GetRateLimit()
    template_values['limit'] = limit
    lists = api.GetLists()
    template_values['lists'] = lists
    tweets = None
    tweets = memcache.get('twitter_home')
    if tweets is None:
      try:
        tweets = api.GetHomeTimeline(count=100)
      except:
        api = None
      if tweets is not None:
        i = 0;
        for tweet in tweets:
          tweets[i].datetime = datetime.datetime.fromtimestamp(time.mktime(time.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y')))
          tweets[i].text = api.ConvertMentions(tweet.text)
          tweets[i].text = api.ExpandBitly(tweet.text)
          i = i + 1
        memcache.set('twitter_home', tweets, 120)
      template_values['tweets'] = tweets
    else:
      template_values['tweets'] = tweets
    template_values['system_version'] = VERSION
    template_values['mode_twitter'] = True;
    template_values['page_title'] = 'Twitter'
    path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'twitter.html')
    self.response.out.write(template.render(path, template_values))
  
class TwitterListHandler(webapp.RequestHandler):
  def get(self, list_id):
    self.session = Session()
    if CheckAuth(self) is False:
      return DoAuth(self, '/twitter/list/' + list_id)
    template_values = {}
    twitter_account = Datum.get('twitter_account')
    twitter_password = Datum.get('twitter_password')
    api = twitter.Api(username=twitter_account, password=twitter_password)
    try:
      limit = api.GetRateLimit()
      template_values['limit'] = limit
      lists = api.GetLists()
      template_values['lists'] = lists
      template_values['list_id'] = int(list_id)
      tweets = None
      tweets = memcache.get('twitter_list_' + list_id)
      if tweets is None:
        try:
          tweets = api.GetListTimeline(user=twitter_account, list_id=list_id)
        except:
          api = None
        if tweets is not None:
          i = 0;
          for tweet in tweets:
            tweets[i].datetime = datetime.datetime.fromtimestamp(time.mktime(time.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y')))
            tweets[i].text = api.ConvertMentions(tweet.text)
            tweets[i].text = api.ExpandBitly(tweet.text)
            i = i + 1
          memcache.set('twitter_list_' + list_id, tweets, 120)
        template_values['tweets'] = tweets
      else:
        template_values['tweets'] = tweets
      template_values['system_version'] = VERSION
      template_values['mode_twitter'] = True;
      template_values['page_title'] = 'Twitter List'
      path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'twitter_list.html')
      self.response.out.write(template.render(path, template_values))
    except:
      template_values['system_version'] = VERSION
      template_values['mode_twitter'] = True;
      template_values['page_title'] = 'Twitter Fail'
      path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'twitter_fail.html')
      self.response.out.write(template.render(path, template_values))

class TwitterMentionsHandler(webapp.RequestHandler):
  def get(self):
    self.session = Session()
    if CheckAuth(self) is False:
      return DoAuth(self, '/twitter/mentions')
    template_values = {}
    twitter_account = Datum.get('twitter_account')
    twitter_password = Datum.get('twitter_password')
    api = twitter.Api(username=twitter_account, password=twitter_password)
    try:
      limit = api.GetRateLimit()
      template_values['limit'] = limit
      lists = api.GetLists()
      template_values['lists'] = lists
      tweets = None
      tweets = memcache.get('twitter_mentions')
      if tweets is None:
        try:
          tweets = api.GetReplies()
        except:
          api = None
        if tweets is not None:
          i = 0;
          for tweet in tweets:
            tweets[i].datetime = datetime.datetime.fromtimestamp(time.mktime(time.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y')))
            tweets[i].text = api.ConvertMentions(tweet.text)
            tweets[i].text = api.ExpandBitly(tweet.text)
            i = i + 1
          memcache.set('twitter_mentions', tweets, 120)
        template_values['tweets'] = tweets
      else:
        template_values['tweets'] = tweets
      template_values['system_version'] = VERSION
      template_values['mode_twitter'] = True;
      template_values['page_title'] = 'Twitter Mentions'
      path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'twitter_mentions.html')
      self.response.out.write(template.render(path, template_values))
    except:
      template_values['system_version'] = VERSION
      template_values['mode_twitter'] = True;
      template_values['page_title'] = 'Twitter Fail'
      path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'twitter_fail.html')
      self.response.out.write(template.render(path, template_values))

class TwitterInboxHandler(webapp.RequestHandler):
  def get(self):
    self.session = Session()
    if CheckAuth(self) is False:
      return DoAuth(self, '/twitter/inbox')
    template_values = {}
    twitter_account = Datum.get('twitter_account')
    twitter_password = Datum.get('twitter_password')
    api = twitter.Api(username=twitter_account, password=twitter_password)
    try:
      limit = api.GetRateLimit()
      template_values['limit'] = limit
      lists = api.GetLists()
      template_values['lists'] = lists
      tweets = None
      tweets = memcache.get('twitter_inbox')
      if tweets is None:
        try:
          tweets = api.GetDirectMessages()
        except:
          api = None
        if tweets is not None:
          i = 0;
          for tweet in tweets:
            tweets[i].datetime = datetime.datetime.fromtimestamp(time.mktime(time.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y')))
            tweets[i].text = api.ConvertMentions(tweet.text)
            tweets[i].text = api.ExpandBitly(tweet.text)
            i = i + 1
          memcache.set('twitter_inbox', tweets, 120)
        template_values['tweets'] = tweets
      else:
        template_values['tweets'] = tweets
      template_values['system_version'] = VERSION
      template_values['mode_twitter'] = True;
      template_values['page_title'] = 'Twitter Inbox'
      path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'twitter_inbox.html')
      self.response.out.write(template.render(path, template_values))
    except:
      template_values['system_version'] = VERSION
      template_values['mode_twitter'] = True;
      template_values['page_title'] = 'Twitter Fail'
      path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'twitter_fail.html')
      self.response.out.write(template.render(path, template_values))

class TwitterUserHandler(webapp.RequestHandler):
  def get(self, user):
    self.session = Session()
    if CheckAuth(self) is False:
      return DoAuth(self, '/twitter/user/' + user)
    template_values = {}
    twitter_account = Datum.get('twitter_account')
    twitter_password = Datum.get('twitter_password')
    api = twitter.Api(username=twitter_account, password=twitter_password)
    try:
      limit = api.GetRateLimit()
      template_values['limit'] = limit
      lists = api.GetLists()
      template_values['lists'] = lists
      if twitter_account == user:
        template_values['me'] = True
      else:
        template_values['me'] = False
      friendships_ab = False
      friendships_ba = False
      friendships_ab = api.GetFriendshipsExists(twitter_account, user)
      friendships_ba = api.GetFriendshipsExists(user, twitter_account)
      tweets = None
      tweets = memcache.get('twitter_user_' + user)
      if tweets is None:
        try:
          tweets = api.GetUserTimeline(user=user, count=100)
        except:
          api = None
        if tweets is not None:
          i = 0;
          for tweet in tweets:
            tweets[i].datetime = datetime.datetime.fromtimestamp(time.mktime(time.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y')))
            tweets[i].text = api.ConvertMentions(tweet.text)
            tweets[i].text = api.ExpandBitly(tweet.text)
            i = i + 1
          memcache.set('twitter_user_' + user, tweets, 120)
        template_values['tweets'] = tweets
      else:
        template_values['tweets'] = tweets
      template_values['friendships_ab'] = friendships_ab
      template_values['friendships_ba'] = friendships_ba
      template_values['twitter_user'] = tweets[0].user
      template_values['system_version'] = VERSION
      template_values['mode_twitter'] = True;
      template_values['page_title'] = 'Twitter User'
      path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'twitter_user.html')
      self.response.out.write(template.render(path, template_values))
    except:
      template_values['system_version'] = VERSION
      template_values['mode_twitter'] = True;
      template_values['page_title'] = 'Twitter Fail'
      path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'twitter_fail.html')
      self.response.out.write(template.render(path, template_values))

class TwitterFriendshipHandler(webapp.RequestHandler):
  def get(self, method, user):
    self.session = Session()
    if CheckAuth(self) is False:
      return DoAuth(self, '/twitter/user/' + user)
    twitter_account = Datum.get('twitter_account')
    if twitter_account == user:
      self.redirect('/twitter/user/' + user)
    else:
      twitter_password = Datum.get('twitter_password')
      api = twitter.Api(username=twitter_account, password=twitter_password)
      if method == 'follow':
        twitter_user = api.CreateFriendship(user)
      if method == 'unfollow':
        twitter_user = api.DestroyFriendship(user)
      self.redirect('/twitter/user/' + user)
  
class TwitterPostHandler(webapp.RequestHandler):
  def post(self):
    self.session = Session()
    if CheckAuth(self) is False:
      return DoAuth(self, '/twitter')
    tweet = self.request.get('status')
    if tweet != '':
      twitter_account = Datum.get('twitter_account')
      twitter_password = Datum.get('twitter_password')
      api = twitter.Api(username=twitter_account, password=twitter_password)
      try:
        api.PostUpdate(tweet)
      except:
        api = None
    memcache.delete('twitter_home')
    self.redirect('/twitter')

  
def main():
  application = webapp.WSGIApplication([
  ('/twitter', TwitterHomeHandler),
  ('/twitter/home', TwitterHomeHandler),
  ('/twitter/mentions', TwitterMentionsHandler),
  ('/twitter/inbox', TwitterInboxHandler),
  ('/twitter/user/([a-zA-Z0-9\-\_]+)', TwitterUserHandler),
  ('/twitter/(follow|unfollow)/([a-zA-Z0-9\-\_]+)', TwitterFriendshipHandler),
  ('/twitter/list/([0-9]+)', TwitterListHandler),
  ('/twitter/post', TwitterPostHandler)
  ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()