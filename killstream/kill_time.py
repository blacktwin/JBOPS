"""
Description: Limit number of plays of TV Show episodes during time of day.
                Idea is to reduce continuous plays while sleeping.
Author: Blacktwin
Requires: requests, plexapi

Enabling Scripts in Tautulli:
Taultulli > Settings > Notification Agents > Add a Notification Agent > Script

Configuration:
Taultulli > Settings > Notification Agents > New Script > Configuration:

 Script Name: kill_time.py
 Set Script Timeout: default
 Description: {Tautulli_description}
 Save

Triggers:
Taultulli > Settings > Notification Agents > New Script > Triggers:

 Check: Playback Start
 Save

Conditions:
Taultulli > Settings > Notification Agents > New Script > Conditions:

 Set Conditions: [{Media Type} | {is} | {episode} ]
 Save

Script Arguments:
Taultulli > Settings > Notification Agents > New Script > Script Arguments:

 Select: Playback Start
 Arguments: {username} {grandparent_rating_key}

 Save
 Close

 Example:

        
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

TIME_DELAY = 60

WATCH_LIMIT = {'user1': 2,
               'user2': 3,
               'user3': 4}

MESSAGE = 'Are you still watching or are you asleep? If not please wait ~{} seconds and try again.'.format(TIME_DELAY)

START_TIME = time(22,00) # 22:00
END_TIME = time(06,00) # 06:00
##/EDIT THESE SETTINGS ##

username = str(sys.argv[1])
grandparent_rating_key = int(sys.argv[2])

TODAY = datetime.today().strftime('%Y-%m-%d')

now = datetime.now()
now_time = now.time()
unix_time = int(ttime())

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)


def get_get_history(username):
    # Get the PlexPy history.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'user': username,
               'start_date': TODAY,
               'order_column': 'date'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']

        ep_watched = [data['watched_status'] for data in res_data
                    if data['grandparent_rating_key'] == grandparent_rating_key and data['watched_status'] == 1]
        if not ep_watched:
            ep_watched = 0
        else:
            ep_watched = sum(ep_watched)

        stopped_time = [data['stopped'] for data in res_data
                        if data['grandparent_rating_key'] == grandparent_rating_key and data['watched_status'] == 1]
        if not stopped_time:
            stopped_time = unix_time
        else:
            stopped_time = stopped_time[0]

        return ep_watched, stopped_time

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))


def kill_session(user):
    for session in plex.sessions():
        # Check for users stream
        if session.usernames[0] == user:
            title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            print('{user} is watching {title} and they might be asleep.'.format(user=user, title=title))
            session.stop(reason=MESSAGE)


watched_count, last_stop = get_get_history(username)

if abs(last_stop - unix_time) > TIME_DELAY:
    print('{} is awake!'.format(username))
    exit()

if watched_count > WATCH_LIMIT[username]:
    print('Checking time range for {}.'.format(username))
    if START_TIME <= now_time or now_time <= END_TIME:
        kill_session(username)
    else:
        print('{} outside of time range.'.format(username))
else:
    print('{} limit is {} but has only watched {} episodes of this show today.'.format(
        username, WATCH_LIMIT[username], watched_count))