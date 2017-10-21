"""
Kill all streams
"""

import requests
from plexapi.server import PlexServer

## EDIT THESE SETTINGS ##
PLEX_TOKEN = 'xxxxx'
PLEX_URL = 'http://localhost:32400'

MESSAGE = 'Because....'
ignore_lst = ('')
##/EDIT THESE SETTINGS ##

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

def kill_session():
    for session in plex.sessions():
        user = session.usernames[0]
        if user not in ignore_lst:
            title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            print("Killing {}'s stream of {} for {}".format(user, title, MESSAGE))
            session.stop(reason=MESSAGE)

kill_session()
