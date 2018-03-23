"""
Kill streams if user has watched too much Plex Today.

Tautulli > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start

Tautulli > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: watch_limit.py

Tautulli > Settings > Notifications > Script > Script Arguments
        {username}
        
"""

import requests
import sys
import datetime
from plexapi.server import PlexServer


## EDIT THESE SETTINGS ##
TAUTULLI_APIKEY = 'xxxx'  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8182/'  # Your Tautulli URL

PLEX_TOKEN = 'xxxxx'
PLEX_URL = 'http://localhost:32400'

WATCH_LIMIT = {'user1': 2,
               'user2': 3,
               'user3': 4}

MESSAGE = 'You have reached your play limit for today.'
##/EDIT THESE SETTINGS ##

username = str(sys.argv[1])

TODAY = datetime.datetime.today().strftime('%Y-%m-%d')

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)


def get_history(username):
    # Get the Tautulli history.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'user': username,
               'start_date': TODAY}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return sum([data['watched_status'] for data in res_data])

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))


def kill_session(user):
    for session in plex.sessions():
        # Check for users stream
        if session.usernames[0] in user:
            title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            print('{user} is watching {title} and they\'ve watched too much today. Killing stream.'
                .format(user=user, title=title))
            session.stop(reason=MESSAGE)


if get_history(username) > WATCH_LIMIT[username]:
    print('User has reached watch limit for today.')
    kill_session(username)
