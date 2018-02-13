"""
Kill streams if user has exceeded time limit on Plex server. Choose to unshare or remove user.

PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: time_limit.py

PlexPy > Settings > Notifications > Script > Script Arguments
        {username}
 
"""

import ConfigParser
import io
import requests
import sys
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

TIME_LIMIT = {'user1': {'d': 1, 'h': 2, 'm': 30, 'remove': True, 'unshare': True},
              'user2': {'d': 0, 'h': 2, 'm': 30, 'remove': False, 'unshare': True},
              'user3': {'d': 0, 'h': 20, 'm': 30, 'remove': True, 'unshare': False}}

MESSAGE = 'You have reached your time limit on my server.'
##/EDIT THESE SETTINGS ##

username = str(sys.argv[1])

total_time = 0

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

sections_lst = [x.title for x in plex.library.sections()]

def get_get_history(username):
    # Get the PlexPy history.
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_history',
               'user': username}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return sum([data['duration'] for data in res_data])

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_history' request failed: {0}.".format(e))


def unshare(user, libraries):
    print('{user} has reached their time limit. Unsharing.'.format(user=user))
    plex.myPlexAccount().updateFriend(user=user, server=plex, removeSections=True, sections=libraries)
    print('Unshared all libraries from {user}.'.format(libraries=libraries, user=user))


def remove_friend(user):
    print('{user} has reached their time limit. Removing.'.format(user=user))
    plex.myPlexAccount().removeFriend(user)
    print('Removed {user}.'.format(user=user))


def kill_session(user):
    for session in plex.sessions():
        # Check for users stream
        if session.usernames[0] in user:
            title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            print('{user} is watching {title} and they\'ve reached their time limit. Killing stream.'
                .format(user=user, title=title))
            session.stop(reason=MESSAGE)


if TIME_LIMIT[username]['d']:
    total_time += TIME_LIMIT[username]['d'] * (24 * 60 * 60)
if TIME_LIMIT[username]['h']:
    total_time += TIME_LIMIT[username]['h'] * (60 * 60)
if TIME_LIMIT[username]['m']:
    total_time += TIME_LIMIT[username]['m'] * 60


if get_get_history(username) > total_time:
    print('User has reached time limit.')
    kill_session(username)
    if TIME_LIMIT[username]['remove']:
        remove_friend(username)
    if TIME_LIMIT[username]['unshare']:
        unshare(username, sections_lst)

