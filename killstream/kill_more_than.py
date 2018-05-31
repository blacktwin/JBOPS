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
SESSION_KEY = int(sys.argv[3])

if USERNAME in ignore_lst:
    print(u"{} ignored.".format(USERNAME))
    exit()

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)


def kill_session(user, ip_address, session_key):
    user_sessions = []
    userip_sessions = []

    for session in plex.sessions():
        username = session.usernames[0]
        address = session.players[0].address
        if username == user:
            user_sessions.append((session))
        if username == user and address == ip_address:
            userip_sessions.append((session))


    if len(user_sessions) >= 2 > len(userip_sessions):
        for session in user_sessions:
            if session_key == session.sessionKey:
                title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
                print(u"Killing {}'s second stream of {} for {}".format(user, title, MESSAGE))
                session.stop(reason=MESSAGE)
#                import httplib, urllib
#                conn = httplib.HTTPSConnection("api.pushover.net:443")
#                conn.request("POST", "/1/messages.json",
#                  urllib.urlencode({
#                    "token": "apptoken",
#                    "user": "usertoken",
#                     "message": ("Killing {}'s second stream of {} for {}".format(user, title, MESSAGE)),
#                  }), { "Content-type": "application/x-www-form-urlencoded" })
#                conn.getresponse()
#                sys.exit(0)
    else:
        print(u"Not killing {}'s second stream. Same IP.".format(user))


kill_session(USERNAME, ADDRESS, SESSION_KEY)

