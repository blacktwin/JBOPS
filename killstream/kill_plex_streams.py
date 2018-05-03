"""
Kill all Plex sessions

"""

import sys
import requests
from plexapi.server import PlexServer
import configparser

# EDIT THESE SETTINGS #
PLEX_URL = ''
PLEX_TOKEN = ''

MESSAGE = 'Because....'
# /EDIT THESE SETTINGS #

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
