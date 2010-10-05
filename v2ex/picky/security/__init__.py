import hashlib

from auth import SECRET

from v2ex.picky import Datum

from v2ex.picky.ext.cookies import Cookies

def CheckAuth(request):
  site_domain = Datum.get('site_domain')
  cookies = Cookies(request, max_age = 86400, path = '/')
  if 'auth' in cookies:
    auth = cookies['auth']
    if str(auth) != hashlib.sha1(SECRET + ':' + site_domain).hexdigest():
      return False
    else:
      return True
  else:
    return False

def DoAuth(request, destination, message = None):
  if message != None:
    request.session['message'] = message
  else:
    request.session['message'] = 'Please sign in first'
  return request.redirect('/writer/auth?destination=' + destination)