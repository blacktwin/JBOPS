#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Refresh the next episode of show once current episode is watched.

Check Tautulli's Watched Percent in Tautulli > Settings > General

1. Tautulli > Settings > Notification Agents > Script > Script Triggers:
    [√] watched
2. Tautulli > Settings > Notification Agents > Script > Gear icon:
    Enter the "Script Folder" where you save the script.
    Select "refresh_next_episode.py" in "Script File".
    Save
3. Tautulli > Settings > Notification Agents > Script > Script Arguments > Watched:
    <episode>{show_name} {episode_num00} {season_num00}</episode>

"""
from __future__ import print_function
from __future__ import unicode_literals

import requests
import sys
from plexapi.server import PlexServer, CONFIG
# pip install plexapi


PLEX_URL = ''
PLEX_TOKEN = ''
PLEX_URL = CONFIG.data['auth'].get('server_baseurl', PLEX_URL)
PLEX_TOKEN = CONFIG.data['auth'].get('server_token', PLEX_TOKEN)

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

show_name = sys.argv[1]
next_ep_num = int(sys.argv[2])
season_num = int(sys.argv[3])
TV_LIBRARY = 'My TV Shows'  # Name of your TV Shows library

current_season = season_num - 1

# Get all seasons from Show
all_seasons = plex.library.section(TV_LIBRARY).get(show_name).seasons()

try:
    # Get all episodes from current season of Show
    all_eps = all_seasons[current_season].episodes()
    # Refresh the next episode
    all_eps[next_ep_num].refresh()
except IndexError:
    try:
        # End of season go to next season
        all_eps = all_seasons[season_num].episodes()
        # Refresh the next season's first episode
        all_eps[0].refresh()
    except IndexError:
        print('End of series')
