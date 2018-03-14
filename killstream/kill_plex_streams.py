"""
Kill all Plex sessions

"""

import sys
import requests
from plexapi.server import PlexServer
import configparser

# EDIT THESE SETTINGS #
PLEX_URL = ''  # leave blank if using config.ini. Overrides config
PLEX_TOKEN = ''  # leave blank if using config.ini. Overrides config

MESSAGE = 'Because....'
# /EDIT THESE SETTINGS #

config = configparser.ConfigParser()
try:
    config.read('../config.ini')
    if not PLEX_URL:
        PLEX_URL = config.get('plex', 'url')
    if not PLEX_TOKEN:
        PLEX_TOKEN = config.get('plex', 'token')
except configparser.NoSectionError:
    sys.exit('Error: No config and missing var values.')

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)


def kill_sessions():
    for session in plex.sessions():
        user = session.usernames[0]
        title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
        print("Killing {}'s stream of {} for {}".format(user, title, MESSAGE))
        session.stop(reason=MESSAGE)


kill_sessions()
