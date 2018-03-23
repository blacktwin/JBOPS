"""
Limit number of plays of TV Show episodes during time of day.
Idea is to reduce continuous plays while sleeping.

Tautulli > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start

Tautulli > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: kill_time.py

Tautulli > Settings > Notifications > Script > Script Arguments
        {username} {media_type} {grandparent_rating_key}
        
"""

import requests
import sys
from datetime import datetime, time
from time import time as ttime
from plexapi.server import PlexServer

## EDIT THESE SETTINGS ##
TAUTULLI_APIKEY = 'xxxx'  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8182/'  # Your Tautulli URL

PLEX_TOKEN = 'xxxx'
PLEX_URL = 'http://localhost:32400'

WATCH_LIMIT = {'user1': 2,
               'user2': 3,
               'user3': 4}

MESSAGE = 'Are you still watching or are you asleep? If not please wait and try again.'

START_TIME = time(22,00) # 22:00
END_TIME = time(06,00) # 06:00
##/EDIT THESE SETTINGS ##

username = str(sys.argv[1])
media_type = str(sys.argv[2])
grandparent_rating_key = str(sys.argv[3])

TODAY = datetime.today().strftime('%Y-%m-%d')

now = datetime.now()
now_time = now.time()
unix_time = int(ttime())

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)


def get_history(username):
    # Get the Tautulli history.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'user': username,
               'start_date': TODAY,
               'order_column': 'date'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        ep_watched = sum([data['watched_status'] for data in res_data
                    if data['grandparent_rating_key'] == grandparent_rating_key and data['watched_status'] == 1])
        stopped_time = [data['stopped'] for data in res_data if data['watched_status' == 1]]
        return [ep_watched, stopped_time[0]]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))


def kill_session(user):
    for session in plex.sessions():
        # Check for users stream
        if session.usernames[0] is user:
            title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            print('{user} is watching {title} and they might be asleep.'.format(user=user, title=title))
            session.stop(reason=MESSAGE)


if media_type is not 'episode':
    exit()

watched_count, last_stop = get_history(username)

if abs(last_stop - unix_time) > 20:
    exit()

if watched_count > WATCH_LIMIT[username]:
    if START_TIME <= now_time or now_time <= END_TIME:
        print('User may be asleep.')
        kill_session(username)
