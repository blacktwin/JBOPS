"""
Kill streams if user has watched too much Plex Today.

PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: watch_limit.py

PlexPy > Settings > Notifications > Script > Script Arguments
        {username}
        
"""

import requests
import ConfigParser
import io
import sys
import datetime
from plexapi.server import PlexServer


# Load the configuration file
with open("../config.ini") as f:
    real_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=False)
config.readfp(io.BytesIO(real_config))

PLEXPY_APIKEY=config.get('plexpy-data', 'PLEXPY_APIKEY')
PLEXPY_URL=config.get('plexpy-data', 'PLEXPY_URL')
PLEX_TOKEN=config.get('plex-data', 'PLEX_TOKEN')
PLEX_URL=config.get('plex-data', 'PLEX_URL')

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


def get_get_history(username):
    # Get the PlexPy history.
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_history',
               'user': username,
               'start_date': TODAY}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return sum([data['watched_status'] for data in res_data])

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_history' request failed: {0}.".format(e))


def kill_session(user):
    for session in plex.sessions():
        # Check for users stream
        if session.usernames[0] in user:
            title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            print('{user} is watching {title} and they\'ve watched too much today. Killing stream.'
                .format(user=user, title=title))
            session.stop(reason=MESSAGE)


if get_get_history(username) > WATCH_LIMIT[username]:
    print('User has reached watch limit for today.')
    kill_session(username)
