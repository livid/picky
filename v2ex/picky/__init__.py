import datetime

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users

formats = set(['html', 'txt', 'markdown'])

class Article(db.Model):
  title = db.StringProperty(required=False, indexed=True)
  title_link = db.StringProperty(required=False, indexed=True)
  title_url = db.StringProperty(required=False, indexed=True)
  parent_url = db.StringProperty(required=False, indexed=True)
  is_page = db.BooleanProperty(required=True, default=False)
  is_for_sidebar = db.BooleanProperty(required=True, default=False)
  content = db.TextProperty()
  content_formatted = db.TextProperty()
  article_set = db.StringProperty(required=False, indexed=True)
  format = db.StringProperty(required=True, default='html', indexed=True)
  created = db.DateTimeProperty(auto_now_add=True)
  last_modified = db.DateTimeProperty(auto_now=True)
  hits = db.IntegerProperty(default=0)
  hits_feed = db.IntegerProperty(default=0)

class Comment(db.Model):
  author_name = db.StringProperty(required=False, indexed=True)
  author_email = db.StringProperty(required=False, indexed=True)
  author_site = db.StringProperty(required=False, indexed=True)
  
class Datum(db.Model):
  title = db.StringProperty(required=False, indexed=True)
  substance = db.TextProperty()
  
  def get(self, name):
    value = memcache.get('datum_' + name)
    if value is not None:
      return value
    else:
      q = db.GqlQuery("SELECT * FROM Datum WHERE title = :1", name)
      if q.count() == 1:
        value = q[0].substance
        memcache.delete('datum_' + name)
        memcache.set('datum_' + name, value, 86400)
      return value
  get = classmethod(get)
    
  def set(self, name, value):
    q = db.GqlQuery("SELECT * FROM Datum WHERE title = :1", name)
    if q.count() == 1:
      d = q[0]
    else:
      d = Datum()
      d.title = name
    d.substance = value
    d.put()
    memcache.delete('datum_' + name)
    memcache.set('datum_' + name, d.substance, 86400)
  set = classmethod(set)