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

# *The* app object
app = Flask(__name__, static_path='/static')

conf = {
  'CACHE_TYPE': 'simple',
   'CACHE_NO_NULL_WARNING': True,
}

cache = Cache(app, config=conf)


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/home")
def home():
    return render_template('home.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"

@app.route('/api/v1/<username>/list')
@cache.cached(timeout=50, key_prefix='gist_user_list')
def gist_user_list(username):
   if username:
     result = gists_for_user(username)
   else:
     result = {"Error": u"Invalid username provided"}

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

    # build the url
    gists_url = 'https://api.github.com/users/{username}/gists'.format(username=username)

    try:
      response = requests.get(gists_url)
    except requests.exceptions.Timeout as e:
      time.sleep(1)
      response = requests.get(gists_url)
    except requests.exceptions.HTTPError as err:
      response = type('lamdbaobject', (object,), {})()
      response.ok = false
      

    # BONUS: What failures could happen?
    # BONUS: Paging? How does this work for users with tons of gists?

    if response.ok:
      return response.json()
    else:
      return {}

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

    username = post_data['username']
    pattern = post_data['pattern']

    result = {}
    gists = gists_for_user(username)
    # BONUS: Handle invalid users?

    for gist in gists:
        # REQUIRED: Fetch each gist and check for the pattern
        # BONUS: What about huge gists?
        # BONUS: Can we cache results in a datastore/db?
        pass

    result['status'] = 'success'
    result['username'] = username
    result['pattern'] = pattern
    result['matches'] = []

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
