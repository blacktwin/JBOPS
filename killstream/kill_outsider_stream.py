"""
Kill stream of user if they are accessing Plex from outside network

Tautulli > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start

Tautulli > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: kill_outsider_stream.py

Tautulli > Settings > Notifications > Script > Script Arguments
        {username}
"""

import requests
from plexapi.server import PlexServer
import sys

## EDIT THESE SETTINGS ##
PLEX_TOKEN = 'xxxxx'
PLEX_URL = 'http://localhost:32400'
MESSAGE = 'Accessing Plex from outside network'

ignore_lst = ('')
## EDIT THESE SETTINGS ##

USERNAME = sys.argv[1]

if USERNAME in ignore_lst:
    print(u"{} ignored.".format(USERNAME))
    exit()

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

def kill_session(user):
    for session in plex.sessions():
        # Check for users stream
        if session.usernames[0] == user and session.players[0].local is False:
            title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            print('{user} is watching {title} and they might be asleep.'.format(user=user, title=title))
            session.stop(reason=MESSAGE)

kill_session(USERNAME)
