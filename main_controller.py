#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import wsgiref.handlers

import urllib, re, cgi, os, httplib, logging, uuid, functools

from google.appengine.ext import webapp
from django.utils import simplejson
from google.appengine.ext.webapp import template

from django.utils import simplejson as json

import model

pattern_http_shorturl = re.compile(r'\<(.*)\>\; rel\=shorturl')
pattern_html_shorturl = re.compile(r'(?i)\<(?:link)\s.*?rel\s*\=\s*[\"\']shorturl[\"\'].*?href\s*\=\s*[\"\'](.*?)[\"\'].*?\>')

## tests to see that the app is runnin on gae, and not on localhost  
def is_production():
  return not os.environ.get('SERVER_SOFTWARE','').startswith('Devel')

def save_user(method):
  
  @functools.wraps(method)
  def wrapper(self, *args, **kwargs):
    import time
    
    anon_user_cookie = self.request.cookies.get('u', None)
    
    self.user = None
    
    self.template_values = {}
    
    if is_production():
        self.template_values['prod']= True
    
    if (anon_user_cookie):
      
      cookie_uuid = urllib.unquote(anon_user_cookie)
      
      self.user = model.User.get_by_key_name("key:" + cookie_uuid)
      
    if (not self.user):
      
      ref = None
      if (self.request.headers.get('Referer') != None and not self.request.headers.get('Referer').startswith(self.request.host_url)):
        ref = self.request.headers.get('Referer')
      
      cookie_uuid = str(uuid.uuid4())
      self.user = model.User(key_name="key:" + cookie_uuid, ref=ref)
      self.user.put()
      
      add_cookie_header(self.response, "u", cookie_uuid, expiration_days = 365)

    return method(self, *args, **kwargs)
              
  return wrapper

def add_cookie_header(response, name, value, expiration_days = 21, expire_date = None):
  import datetime, urllib

  if expire_date:
    expiration_date = expire_date.strftime('%a, %d-%b-%Y %H:%M:%S')
  else: 
    expiration_date = (datetime.date.today() + datetime.timedelta(expiration_days)).strftime('%a, %d-%b-%Y %H:%M:%S')
  response.headers.add_header('Set-Cookie', 
          '%s=%s; expires=%s GMT; path=/;' % (name, urllib.quote(value), expiration_date))
  

def find_shorturl(longurl):
  
  links = ()
  body = ""
  shorturl = None
  
  logging.info("longurl:" + str(longurl))

  f = urllib.urlopen(longurl)
  links = f.headers.getallmatchingheaders('link')
  #logging.info(links)
  body = f.read()
  f.close()

  # check for HTTP Link: header
  error = warning = None
  for link in links:
    # shorturl warning
    m = pattern_http_shorturl.search(link)
    if (m): 
      return m.group(1), "http_header"
      
  # logging.info(body)

  if (longurl):
    m = pattern_html_shorturl.search(body)
    if (m): 
      return m.group(1), "html_body"
      
  return None, None


class MainHandler(webapp.RequestHandler):

  def get(self):
    
    self.template_values = {}
    
    self.template_values['api_base_url'] = "http://relshorturl.appspot.com"
    self.template_values['api_base_domain'] = "relshorturl.appspot.com"
    
    path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
    self.response.out.write(template.render(path, self.template_values))

class FormHandler(webapp.RequestHandler):

  @save_user
  def get(self):
    
    longurl = self.request.get("url", None)
    
    if (longurl and (not longurl.startswith("http://") and not longurl.startswith("https://"))):
      longurl = "http://" + longurl
    
    shorturl = None
    shorturl_source = None
    
    if (longurl):
      try:
        shorturl, shorturl_source = find_shorturl(longurl)
      except:
        pass
      
    logging.info(longurl, shorturl)
    
    self.template_values['api_base_url'] = "http://relshorturl.appspot.com"
    self.template_values['api_base_domain'] = "relshorturl.appspot.com"
    
    if (longurl):
      self.template_values['shorturl'] = shorturl
      
      url = model.Url(user=self.user, longurl=longurl, userip=self.request.remote_addr)
      url.put()
      
      path = os.path.join(os.path.dirname(__file__), 'templates/iframe_result.html')
      self.response.out.write(template.render(path, self.template_values))
    else:
      path = os.path.join(os.path.dirname(__file__), 'templates/iframe_form.html')
      self.response.out.write(template.render(path, self.template_values))

class ApiHandler(webapp.RequestHandler):

  @save_user
  def get(self):
    
    longurl = self.request.get("url", None)
    
    if (longurl and (not longurl.startswith("http://") and not longurl.startswith("https://"))):
      longurl = "http://" + longurl
      
    if (longurl):
      try:
        shorturl, shorturl_source = find_shorturl(longurl)
      except:
        pass      
    
    if (shorturl):
      self.response.out.write(json.dumps({'success': True,"shorturl": shorturl,}))
    else:
      self.response.out.write(json.dumps({'success': False,}))
          
def main():
  application = webapp.WSGIApplication([('/', MainHandler),
                                        ('/iframe', FormHandler),
                                        ('/api', ApiHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
