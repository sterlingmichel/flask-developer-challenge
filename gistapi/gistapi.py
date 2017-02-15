# coding=utf-8
"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""

import requests
from flask import Flask, jsonify, json, request, Response, render_template, copy_current_request_context,  redirect, url_for
from flask_cache import Cache
import time
import re
import datastore.core

# *The* app object
app = Flask(__name__, static_path='/static')

conf = {
  'CACHE_TYPE': 'simple',
  'CACHE_NO_NULL_WARNING': True
}

cache = Cache(app, config=conf)
ds = datastore.DictDatastore() # in memory


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Cache-Control'] = 'no-cache, no-store' #'public, max-age=0'
    return response

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route("/home")
def home():
    return render_template('home.html')

@app.errorhandler(404)
def not_found(error=None):
    message = {
            'status': 404,
            'error': error,
            'message': 'Not Found: ' + request.url,
    }
    return render_template('404.html', message=message), 404

@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"

@app.route('/api/v1/gist/<username>/list', methods = ['GET'])
#@cache.cached(timeout=10, key_prefix='gist_user_list')
def gist_user_list(username):
   if username:
     result = gists_for_user(username)
   else:
     return not_found("Invalid username provided")

   js = json.dumps(result, indent=4, sort_keys=True)

   resp = Response(js, status=200, mimetype='application/json')

   return resp

def gists_for_user(username):
    """Provides the list of gist metadata for a given user.

    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.

    Args:
        username (string): the user to query gists for

    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """

    rs = []

    def loop(url=None):
      # build the url
      per_page = 2
      page = 1
      gists_url = url or 'https://api.github.com/users/{username}/gists?per_page={per_page}&page={page}'.format(per_page=per_page, page=page, username=username)
      gists_url += "&client_id=%s&client_secret=%s" %("3cc58ae648e5bfd676cf", "f908a9ddcebdbc36d38c1fe902f98cb12d15c44c")

      try:
        response = requests.get(gists_url)
      except requests.exceptions.Timeout as e:
        time.sleep(1)
        response = requests.get(url)
      except requests.exceptions.HTTPError as err:
        response = type('lamdbaobject', (object,), {})()
        response.ok = false
      
      if response.ok:
        # grab the data response
        rs.extend(response.json())

        if response.headers.get('Link', None):
          # parse the for the next url
          links = response.headers['Link'].split(',')
          
          # extra the url
          next_url = re.match('<(.*)>; rel="next"', links[0])

          # BONUS: What about huge gists?
          if next_url:
            gists_url = next_url.groups()[0]
            loop(gists_url)

        else:
          rs.extend(response.json())

      else:
        # BONUS: Handle invalid users?
        return response.json()

      return rs

    return loop()

@app.route("/api/v1/search", methods=['POST'])
def search():
    """Provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """

    post_data = request.get_json()

    # BONUS: Validate the arguments?
    if post_data:
      if not('username' in post_data):
        return jsonify({'Error': 'Invalid user is given'})

      if not('pattern' in post_data):
        return jsonify({'Error': 'Invalid pattern is given'})

    else:
      return jsonify({"Error": "'application/json' was not set for mine-type and accept"})
 
    username = post_data['username']
    pattern = post_data['pattern']

    result = {}
   
    # set the key
    dsKey = datastore.Key(username)

    # BONUS: Can we cache results in a datastore/db?
    # validate above
    if ds.contains(dsKey):
       gists = ds.get(dsKey)
    else:
      gists = gists_for_user(username)

      # store a key for the datastore
      ds.put(dsKey, gists)

    matches = []
    for gist in gists:
       # REQUIRED: Fetch each gist and check for the pattern
       txt_version = str(gist)
       search_gist = re.findall(pattern, txt_version, re.IGNORECASE)
       if search_gist:
         matches.append(gist)

    result['status'] = 'success'
    result['username'] = username
    result['pattern'] = pattern
    result['matches'] = matches

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
