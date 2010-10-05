#!/usr/bin/env python
# coding=utf-8

import os
import time
import urllib
import wsgiref.handlers
import markdown
import hashlib

from auth import SECRET
from version import *

from v2ex.picky import Article
from v2ex.picky import Datum

from v2ex.picky import formats as CONTENT_FORMATS
from v2ex import TWITTER_API_ROOT

from v2ex.picky.misc import reminder
from v2ex.picky.misc import message

from v2ex.picky.security import CheckAuth, DoAuth

from v2ex.picky.ext import feedparser
from v2ex.picky.ext import twitter
from v2ex.picky.ext.sessions import Session
from v2ex.picky.ext.cookies import Cookies

from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import users

from django.core.paginator import ObjectPaginator, InvalidPage
from django.utils import simplejson

# GLOBALS

PAGE_SIZE = 15

class WriterAuthHandler(webapp.RequestHandler):
  def get(self):
    self.session = Session()
    site_domain = Datum.get('site_domain')
    site_domain_sync = Datum.get('site_domain_sync')
    site_name = Datum.get('site_name')
    site_author = Datum.get('site_author')
    site_slogan = Datum.get('site_slogan')
    site_analytics = Datum.get('site_analytics')
    if site_domain is None:
      site_domain = os.environ['HTTP_HOST']
      Datum.set('site_domain', os.environ['HTTP_HOST'])
    if site_domain_sync is None:
      site_domain_sync = os.environ['HTTP_HOST']
      Datum.set('site_domain_sync', os.environ['HTTP_HOST'])
    template_values = {}
    
    if 'message' in self.session:
      message = self.session['message']
      del self.session['message']
    else:
      message = None
    template_values['message'] = message
    destination = None
    destination = self.request.get('destination')
    template_values['destination'] = destination
    template_values['system_version'] = VERSION
    path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'auth.html')
    self.response.out.write(template.render(path, template_values))
    
  def post(self):
    self.session = Session()
    site_domain = Datum.get('site_domain')
    site_domain_sync = Datum.get('site_domain_sync')
    site_name = Datum.get('site_name')
    site_author = Datum.get('site_author')
    site_slogan = Datum.get('site_slogan')
    site_analytics = Datum.get('site_analytics')
    destination = self.request.get('destination')
    if (str(destination) == ''):
      destination = None
    if site_domain is None:
      site_domain = os.environ['HTTP_HOST']
      Datum.set('site_domain', os.environ['HTTP_HOST'])
    if site_domain_sync is None:
      site_domain_sync = os.environ['HTTP_HOST']
      Datum.set('site_domain_sync', os.environ['HTTP_HOST'])
    cookies = Cookies(self, max_age = 86400, path = '/')
    s = self.request.get('secret')
    sha1 = hashlib.sha1(s).hexdigest()
    if (sha1 == SECRET):
      cookies['auth'] = hashlib.sha1(SECRET + ':' + site_domain).hexdigest()
      if destination is None:
        self.redirect('/writer/overview')
      else:
        self.redirect(str(destination))
    else:
      self.session['message'] = "Your entered secret passphrase isn't correct"
      if destination is None:
        self.redirect('/writer/auth')
      else:
        self.redirect('/writer/auth?destination=' + str(destination))

class WriterSignoutHandler(webapp.RequestHandler):
  def get(self):
    self.session = Session()
    cookies = Cookies(self, max_age = 3600, path = '/')
    if 'auth' in cookies:
      del cookies['auth']
    site_domain = Datum.get('site_domain')
    site_domain_sync = Datum.get('site_domain_sync')
    site_name = Datum.get('site_name')
    site_author = Datum.get('site_author')
    site_slogan = Datum.get('site_slogan')
    site_analytics = Datum.get('site_analytics')
    template_values = {}
    template_values['site_name'] = site_name
    template_values['site_domain'] = site_domain
    template_values['system_version'] = VERSION
    path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'signout.html')
    self.response.out.write(template.render(path, template_values))

class WriterOverviewHandler(webapp.RequestHandler):
  def get(self):
    self.session = Session()
    if CheckAuth(self) is False:
      return DoAuth(self, '/writer/overview')
    site_domain = Datum.get('site_domain')
    site_domain_sync = Datum.get('site_domain_sync')
    site_name = Datum.get('site_name')
    site_author = Datum.get('site_author')
    site_slogan = Datum.get('site_slogan')
    site_analytics = Datum.get('site_analytics')
    if site_domain is None:
      site_domain = os.environ['HTTP_HOST']
      Datum.set('site_domain', os.environ['HTTP_HOST'])
    if site_domain_sync is None:
      site_domain_sync = os.environ['HTTP_HOST']
      Datum.set('site_domain_sync', os.environ['HTTP_HOST'])
    articles = memcache.get('writer_articles')
    if articles is None:
      articles = Article.all().order('-created')
      memcache.set('writer_articles', articles, 86400)
    paginator = ObjectPaginator(articles, PAGE_SIZE)
    try:
      page = int(self.request.get('page', 0))
      articles = paginator.get_page(page)
    except InvalidPage:
      articles = paginator.get_page(int(paginator.pages - 1))
    if paginator.pages > 1:
      is_paginated = True
    else:
      is_paginated = False
    if site_domain is None or site_name is None or site_author is None:
      site_configured = False
    else:
      site_configured = True
    if is_paginated:
      self.session['page'] = page
    urls = memcache.get('writer_urls')
    if urls is None:
      everything = Article.all().order('-title_url')
      urls = []
      for article in everything:
        urls.append(article.title_url)
      memcache.set('writer_urls', urls, 86400)
    template_values = {
      'site_configured' : site_configured,
      'is_paginated' : is_paginated,
      'page_size' : PAGE_SIZE,
      'page_has_next' : paginator.has_next_page(page),
      'page_has_previous' : paginator.has_previous_page(page),
      'page' : page,
      'next' : page + 1,
      'previous' : page - 1,
      'pages' : paginator.pages,
      'articles' : articles,
      'articles_total' : len(articles),
      'page_range' : range(0, paginator.pages),
      'urls' : urls
    }
    if site_analytics is not None:
      template_values['site_analytics'] = site_analytics
    if site_domain_sync is None:
      q = site_domain
    else:
      q = site_domain + ' OR ' + site_domain_sync
    mentions_web = memcache.get('mentions_web')
    if mentions_web is None:
      try:
        mentions_web = feedparser.parse('http://blogsearch.google.com/blogsearch_feeds?hl=en&q=' + urllib.quote('link:' + Datum.get('site_domain')) + '&ie=utf-8&num=10&output=atom')
        memcache.add('mentions_web', mentions_web, 600)
      except:
        mentions_web = None
    if mentions_web is not None:
      template_values['mentions_web'] = mentions_web.entries
    #mentions_twitter = memcache.get('mentions_twitter')
    #if mentions_twitter is None:    
    #  try:
    #    result = urlfetch.fetch('http://search.twitter.com/search.json?q=' + urllib.quote(q))
    #    if result.status_code == 200:
    #      mentions_twitter = simplejson.loads(result.content)
    #      memcache.add('mentions_twitter', mentions_twitter, 600)
    #  except:
    #    mentions_twitter = None
    #if mentions_twitter is not None:
    #  if len(mentions_twitter['results']) > 0:
    #    template_values['mentions_twitter'] = mentions_twitter['results']
    template_values['system_version'] = VERSION
    if 'message' in self.session:
      template_values['message'] = self.session['message']
      del self.session['message']
    path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'overview.html')
    self.response.out.write(template.render(path, template_values))

class WriterSettingsHandler(webapp.RequestHandler):
  def get(self):
    self.session = Session()
    if CheckAuth(self) is False:
      return DoAuth(self, '/writer/settings')
    site_domain = Datum.get('site_domain')
    site_domain_sync = Datum.get('site_domain_sync')
    site_name = Datum.get('site_name')
    site_author = Datum.get('site_author')
    site_slogan = Datum.get('site_slogan')
    site_analytics = Datum.get('site_analytics')
    site_default_format = Datum.get('site_default_format')
    if site_default_format is None:
      site_default_format = 'html'
    twitter_account = Datum.get('twitter_account')
    twitter_password = Datum.get('twitter_password')
    twitter_sync = None
    q = db.GqlQuery("SELECT * FROM Datum WHERE title = 'twitter_sync'")
    if q.count() == 1:
      twitter_sync = q[0].substance
    if (twitter_sync == 'True'):
      twitter_sync = True
    else:
      twitter_sync = False
    feed_url = Datum.get('feed_url')
    themes = os.listdir(os.path.join(os.path.dirname(__file__), 'tpl', 'themes'))
    site_theme = Datum.get('site_theme')
    template_values = {
      'site_domain' : site_domain,
      'site_domain_sync' : site_domain_sync,
      'site_name' : site_name,
      'site_author' : site_author,
      'site_slogan' : site_slogan,
      'site_analytics' : site_analytics,
      'site_default_format' : site_default_format,
      'twitter_account' : twitter_account,
      'twitter_password' : twitter_password,
      'twitter_sync' : twitter_sync,
      'feed_url' : feed_url,
      'themes' : themes,
      'site_theme' : site_theme
    }
    if site_analytics is not None:
      template_values['site_analytics'] = site_analytics
    template_values['system_version'] = VERSION
    path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'settings.html')
    self.response.out.write(template.render(path, template_values))
    
  def post(self):
    self.session = Session()
    if CheckAuth(self) is False:
      return DoAuth(self, '/writer/settings')
    Datum.set('site_domain', self.request.get('site_domain'))
    Datum.set('site_domain_sync', self.request.get('site_domain_sync'))
    Datum.set('site_name', self.request.get('site_name'))
    Datum.set('site_author', self.request.get('site_author'))
    Datum.set('site_slogan', self.request.get('site_slogan'))
    Datum.set('site_analytics', self.request.get('site_analytics'))
    if self.request.get('site_default_format') not in CONTENT_FORMATS:
      Datum.set('site_default_format', 'html')
    else:
      Datum.set('site_default_format', self.request.get('site_default_format'))
    Datum.set('twitter_account', self.request.get('twitter_account'))
    Datum.set('twitter_password', self.request.get('twitter_password'))
    q = db.GqlQuery("SELECT * FROM Datum WHERE title = 'twitter_sync'")
    if q.count() == 1:
      twitter_sync = q[0]
    else:
      twitter_sync = Datum()
      twitter_sync.title = 'twitter_sync'
    twitter_sync.substance = self.request.get('twitter_sync')
    if twitter_sync.substance == 'True':
      twitter_sync.substance = 'True'
    else:
      twitter_sync.substance = 'False'
    twitter_sync.put()
    Datum.set('feed_url', self.request.get('feed_url'))
    themes = os.listdir(os.path.join(os.path.dirname(__file__), 'tpl', 'themes'))
    if self.request.get('site_theme') in themes:
      Datum.set('site_theme', self.request.get('site_theme'))
    else:
      Datum.set('site_theme', 'default')
    memcache.delete('mentions_twitter')
    self.redirect('/writer/settings')
    
class WriterWriteHandler(webapp.RequestHandler):
  def get(self, key = ''):
    self.session = Session()
    if CheckAuth(self) is False:
      return DoAuth(self, '/writer/new')
    site_domain = Datum.get('site_domain')
    site_domain_sync = Datum.get('site_domain_sync')
    site_name = Datum.get('site_name')
    site_author = Datum.get('site_author')
    site_slogan = Datum.get('site_slogan')
    site_analytics = Datum.get('site_analytics')
    site_default_format = Datum.get('site_default_format')
    if 'page' in self.session:
      page = self.session['page']
    else:
      page = 0
    if (key):
      article = db.get(db.Key(key))
      template_values = {
        'site_default_format' : site_default_format,
        'article' : article,
        'page_mode' : 'edit',
        'page_title' : 'Edit Article',
        'page_reminder': reminder.writer_write,
        'page' : page
      }
    else:
      template_values = {
        'site_default_format' : site_default_format,
        'page_mode' : 'new',
        'page_title' : 'New Article',
        'page_reminder': reminder.writer_write,
        'page' : page
      }
    if site_analytics is not None:
      template_values['site_analytics'] = site_analytics
    template_values['system_version'] = VERSION
    path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'write.html')
    self.response.out.write(template.render(path, template_values))

class WriterRemoveHandler(webapp.RequestHandler):
  def get(self, key = ''):
    if (key):
      self.session = Session()
      if CheckAuth(self) is False:
        return DoAuth(self, '/writer/remove/' + key)
      article = db.get(db.Key(key))
      article.delete()
    self.redirect('/writer/overview')

class WriterSynchronizeHandler(webapp.RequestHandler):
  def get(self):
    self.redirect('/writer')
    
  def post(self, key = ''):
    self.session = Session()
    if CheckAuth(self) is False:
      return DoAuth(self, '/writer')
    site_domain = Datum.get('site_domain')
    site_domain_sync = Datum.get('site_domain_sync')
    site_name = Datum.get('site_name')
    site_author = Datum.get('site_author')
    site_slogan = Datum.get('site_slogan')
    site_analytics = Datum.get('site_analytics')
    site_default_format = Datum.get('site_default_format')
    if 'page' in self.session:
      page = self.session['page']
    else:
      page = 0
    site_default_format = Datum.get('site_default_format')
    if (self.request.get('content') != ''):
      if (key):
        article = db.get(db.Key(key))
        article.title = self.request.get('title')
        article.title_link = self.request.get('title_link')
        article.title_url = self.request.get('title_url')
        article.parent_url = self.request.get('parent_url')
        article.content = self.request.get('content')
        article.article_set = self.request.get('article_set')
        article.format = self.request.get('format')
        if article.format not in CONTENT_FORMATS:
          article.format = site_default_format
        if article.format == 'markdown':
          article.content_formatted = markdown.markdown(article.content)
        if (self.request.get('is_page') == 'True'):
          article.is_page = True
        else:
          article.is_page = False
        if (self.request.get('is_for_sidebar') == 'True'):
          article.is_for_sidebar = True
        else:
          article.is_for_sidebar = False
        article.put()
        self.session['message'] = '<div style="float: right;"><a href="http://' + site_domain + '/' + article.title_url + '" target="_blank" class="super normal button">View Now</a></div>Changes has been saved into <a href="/writer/edit/' + key + '">' + article.title + '</a>'
      else:
        article = Article()
        article.title = self.request.get('title')
        article.title_link = self.request.get('title_link')
        article.title_url = self.request.get('title_url')
        article.parent_url = self.request.get('parent_url')
        article.content = self.request.get('content')
        article.article_set = self.request.get('article_set')
        article.format = self.request.get('format')
        if article.format not in CONTENT_FORMATS:
          article.format = site_default_format
        if article.format == 'markdown':
          article.content_formatted = markdown.markdown(article.content)
        if (self.request.get('is_page') == 'True'):
          article.is_page = True
        else:
          article.is_page = False
        if (self.request.get('is_for_sidebar') == 'True'):
          article.is_for_sidebar = True
        else:
          article.is_for_sidebar = False
        article.put()
        self.session['message'] = '<div style="float: right;"><a href="http://' + site_domain + '/' + article.title_url + '" target="_blank" class="super normal button">View Now</a></div>New article <a href="/writer/edit/' + str(article.key()) + '">' + article.title + '</a> has been created'
        # Ping Twitter
        twitter_sync = Datum.get('twitter_sync')
        if twitter_sync == 'True' and article.is_page is False:  
          twitter_account = Datum.get('twitter_account')
          twitter_password = Datum.get('twitter_password')
          if twitter_account != '' and twitter_password != '':
            api = twitter.Api(username=twitter_account, password=twitter_password)
            try:
              status = api.PostUpdate(article.title + ' http://' + site_domain_sync + '/' + article.title_url + ' (Sync via @projectpicky)')
            except:
              api = None
      obsolete = ['archive', 'archive_output', 'feed_output', 'index', 'index_output', 'writer_articles', 'writer_urls']
      memcache.delete_multi(obsolete)
      Datum.set('site_updated', time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
      # Ping Google Blog Search
      if site_domain.find('localhost') == -1:
        try:
          google_ping = 'http://blogsearch.google.com/ping?name=' + urllib.quote(Datum.get('site_name')) + '&url=http://' + urllib.quote(Datum.get('site_domain')) + '/&changesURL=http://' + urllib.quote(Datum.get('site_domain')) + '/sitemap.xml'
          result = urlfetch.fetch(google_ping)
        except:
          taskqueue.add(url='/writer/ping')
      self.redirect('/writer/overview?page=' + str(page))
    else:
      article = Article()
      article.title = self.request.get('title')
      article.title_link = self.request.get('title_link')
      article.title_url = self.request.get('title_url')
      article.content = self.request.get('content')
      article.article_set = self.request.get('article_set')
      article.format = self.request.get('format')
      if article.format not in CONTENT_FORMATS:
        article.format = site_default_format
      if (self.request.get('is_page') == 'True'):
        article.is_page = True
      else:
        article.is_page = False
      if (self.request.get('is_for_sidebar') == 'True'):
        article.is_for_sidebar = True
      else:
        article.is_for_sidebar = False
      template_values = {
        'site_default_format' : site_default_format,
        'article' : article,
        'page_mode' : 'new',
        'page_title' : 'New Article',
        'page_reminder': reminder.writer_write,
        'message' : message.content_empty,
        'user_email' : user.email(),
        'page' : page
      }
      if site_analytics is not None:
        template_values['site_analytics'] = site_analytics
      template_values['system_version'] = VERSION
      path = os.path.join(os.path.dirname(__file__), 'tpl', 'writer', 'write.html')
      self.response.out.write(template.render(path, template_values))
      
class WriterQuickFindHandler(webapp.RequestHandler):
  def post(self):
    self.session = Session()
    if CheckAuth(self) is False:
      return
    qf = self.request.get('qf')
    if qf is not None:
      q = db.GqlQuery('SELECT __key__ FROM Article WHERE title_url = :1', qf)
      if q.count() == 1:
        self.redirect('/writer/edit/' + str(q[0]))
      else:
        self.redirect(self.request.headers['REFERER'])
    else:
      self.redirect(self.request.headers['REFERER'])

class WriterPingHandler(webapp.RequestHandler):
  def get(self):
    site_domain = Datum.get('site_domain')
    site_name = Datum.get('site_name')
    try:
      google_ping = 'http://blogsearch.google.com/ping?name=' + urllib.quote(Datum.get('site_name')) + '&url=http://' + urllib.quote(Datum.get('site_domain')) + '/&changesURL=http://' + urllib.quote(Datum.get('site_domain')) + '/index.xml'
      result = urlfetch.fetch(google_ping)
      if result.status_code == 200:
        self.response.out.write('OK: Google Blog Search Ping: ' + google_ping)
      else:
        self.response.out.write('Reached but failed: Google Blog Search Ping: ' + google_ping)
    except:
      self.response.out.write('Failed: Google Blog Search Ping: ' + google_ping)
  
def main():
  application = webapp.WSGIApplication([
  ('/writer', WriterOverviewHandler),
  ('/writer/auth', WriterAuthHandler),
  ('/writer/signout', WriterSignoutHandler),
  ('/writer/overview', WriterOverviewHandler),
  ('/writer/settings', WriterSettingsHandler),
  ('/writer/new', WriterWriteHandler),
  ('/writer/save', WriterSynchronizeHandler),
  ('/writer/ping', WriterPingHandler),
  ('/writer/update/([0-9a-zA-Z\-\_]+)', WriterSynchronizeHandler),
  ('/writer/edit/([0-9a-zA-Z\-\_]+)', WriterWriteHandler),
  ('/writer/remove/([0-9a-zA-Z\-\_]+)', WriterRemoveHandler),
  ('/writer/quick/find', WriterQuickFindHandler)
  ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()