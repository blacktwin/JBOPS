#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Pull Movie and TV Show poster images from Plex.

Saves the poster images to Movie and TV Show directories in scripts working
directory.

Author: Blacktwin
Requires: plexapi

 Example:
    python plex_api_poster_pull.py

"""
from __future__ import print_function
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from plexapi.server import PlexServer, CONFIG
import requests
import re
import os
import urllib.request, urllib.parse, urllib.error

library_name = ['Movies', 'TV Shows']  # Your library names

PLEX_URL = ''
PLEX_TOKEN = ''
if not PLEX_URL:
    PLEX_URL = CONFIG.data['auth'].get('server_baseurl', '')

if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token', '')


sess = requests.Session()
# Ignore verifying the SSL certificate
sess.verify = False  # '/path/to/certfile'
# If verify is set to a path to a directory,
# the directory must have been processed using the c_rehash utility supplied
# with OpenSSL.
if sess.verify is False:
    # Disable the warning that the request is insecure, we know that...
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

# Create paths for Movies and TV Shows inside current directory
movie_path = '{}/Movies'.format(os.path.dirname(__file__))
if not os.path.isdir(movie_path):
    os.mkdir(movie_path)

show_path = '{}/TV Shows'.format(os.path.dirname(__file__))
if not os.path.isdir(show_path):
    os.mkdir(show_path)


# Get all movies or shows from LIBRARY_NAME
for library in library_name:
    for child in plex.library.section(library).all():
        # Clean names of special characters
        name = re.sub('\W+', ' ', child.title)
        # Add (year) to name
        name = '{} ({})'.format(name, child.year)
        # Pull URL for poster
        thumb_url = '{}{}?X-Plex-Token={}'.format(PLEX_URL, child.thumb, PLEX_TOKEN)
        # Select path based on media_type
        if child.type == 'movie':
            image_path = u'{}/{}.jpg'.format(movie_path, name)
        elif child.type == 'show':
            image_path = u'{}/{}.jpg'.format(show_path, name)
        # Check if file already exists
        if os.path.isfile(image_path):
            print("ERROR, %s already exist" % image_path)
        else:
            # Save to directory
            urllib.request.urlretrieve(thumb_url, image_path)
