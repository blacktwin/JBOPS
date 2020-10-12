#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Download theme songs from Plex TV Shows.

Theme songs are mp3 and named by shows as displayed by Plex.
Songs are saved in a 'Theme Songs' directory located in script's path.

"""
from __future__ import unicode_literals


from future import standard_library
standard_library.install_aliases()
from plexapi.server import PlexServer, CONFIG
# pip install plexapi
import os
import re
import urllib.request, urllib.parse, urllib.error
import requests

# ## Edit ##
PLEX_URL = ''
PLEX_TOKEN = ''
PLEX_URL = CONFIG.data['auth'].get('server_baseurl', PLEX_URL)
PLEX_TOKEN = CONFIG.data['auth'].get('server_token', PLEX_TOKEN)

TV_LIBRARY = 'TV Shows'  # Name of your TV Show library
# ## /Edit ##

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

# Theme Songs url
themes_url = 'http://tvthemes.plexapp.com/{}.mp3'

# Create /Theme Songs/ directory in same path as script.
out_path = os.path.join(os.path.dirname(__file__), 'Theme Songs')
if not os.path.isdir(out_path):
    os.mkdir(out_path)

# Get episodes from TV Shows
for show in plex.library.section(TV_LIBRARY).all():
    # Remove special characters from name
    filename = '{}.mp3'.format(re.sub('\W+', ' ', show.title))
    # Set output path
    theme_path = os.path.join(out_path, filename)
    # Get tvdb_if from first episode, no need to go through all episodes
    tvdb_id = show.episodes()[0].guid.split('/')[2]
    # Download theme song to output path
    urllib.request.urlretrieve(themes_url.format(tvdb_id), theme_path)
