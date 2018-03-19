"""
If user has 2* or more concurrent streams and the IP of the 2nd stream differs from 1st kill 2nd.
If 2nd stream IP is the same as 1st stream don't kill.
*Tautulli > Settings > Notification> User Concurrent Stream Threshold
    The number of concurrent streams by a single user for Tautulli to trigger a notification. Minimum 2.
Tautulli > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on user concurrent streams

Tautulli > Settings > Notification Agents > Scripts > Gear icon:
        Playback User Concurrent Streams: kill_more_than.py

Tautulli > Settings > Notifications > Script > Script Arguments
        {username} {ip_address} {session_key}
"""

import requests
import sys
from plexapi.server import PlexServer

## EDIT THESE SETTINGS ##
PLEX_TOKEN = 'xxxxx'
PLEX_URL = 'http://localhost:32400'

MESSAGE = 'Because....too many streams'
ignore_lst = ('')
## EDIT THESE SETTINGS ##

# 2nd stream information is passed
USERNAME = sys.argv[1]
ADDRESS = sys.argv[2]
SESSION_KEY = sys.argv[3]

if USERNAME in ignore_lst:
    print(u"{} ignored.".format(USERNAME))
    exit()

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)


def kill_session(user, ip_address, session_key):
    user_sessions = []

    for session in plex.sessions():
        username = session.usernames[0]
        address = session.players[0].address
        if username == user and address == ip_address:
            user_sessions.append((session))

    if len(user_sessions) > 1:
        for session in user_sessions:
            if session_key == session.sessionKey:
                title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
                print(u"Killing {}'s second stream of {} for {}".format(username, title, MESSAGE))
                session.stop(reason=MESSAGE)
    else:
        for session in user_sessions:
            username = session.usernames[0]
            print(u"Not killing {}'s second stream. Same IP".format(username))


kill_session(USERNAME, ADDRESS, SESSION_KEY)
