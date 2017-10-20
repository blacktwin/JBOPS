"""
If user has 2* or more concurrent streams and the IP of the 2nd stream differs from 1st kill 2nd.
If 2nd stream IP is the same as 1st stream don't kill.
*PlexPy > Settings > Notification> User Concurrent Stream Threshold
    The number of concurrent streams by a single user for PlexPy to trigger a notification. Minimum 2.
PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on user concurrent streams

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback User Concurrent Streams: kill_more_than.py

PlexPy > Settings > Notifications > Script > Script Arguments
        {user} {ip_address}
"""

import requests
import sys
from plexapi.server import PlexServer

## EDIT THESE SETTINGS ##
PLEX_TOKEN = 'xxxx'
PLEX_URL = 'http://localhost:32400'

MESSAGE = 'Because....too many streams'
##/EDIT THESE SETTINGS ##

# 2nd stream information is passed
USERNAME = sys.argv[1]
ADDRESS = sys.argv[2]

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)


def kill_session(session_key, reason):
    for session in plex.sessions():
        # Check for users session key
        if session.sessionKey == session_key:
            title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            print('{user} is watching {title} and they might be asleep.'.format(user=user, title=title))
            session.stop(reason=reason)


user_sessions = []

for session in plex.sessions():
    username = session.usernames[0]
    ip_address = session.players[0].address
    if username == USERNAME and ip_address == ADDRESS:
        sess_key = session.sessionKey
        title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
        user_sessions.append((sess_key, username, title))

if len(user_sessions) == 1:
    for session in user_sessions:
        print(u"Killing {}'s second stream of {} for {}".format(session[1], session[2], MESSAGE))
        kill_session(session[0], MESSAGE)
else:
    for session in user_sessions:
        print(u"Not killing {}'s second stream. Same IP".format(session[1]))
