"""
Kill streams if user has played too much Plex Today.

Tautulli > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start

Tautulli > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: play_limit.py

Tautulli > Settings > Notifications > Script > Script Arguments
        {username} {section_id}

"""

import requests
import sys
import datetime
from plexapi.server import PlexServer


## EDIT THESE SETTINGS ##
TAUTULLI_APIKEY = 'xxxxx'  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8182/'  # Your Tautulli URL

PLEX_TOKEN = 'xxxxx'
PLEX_URL = 'http://localhost:32400'

PLAY_LIMIT = {'user1':
                  [{'section_id': 2, 'limit': 0},
                   {'section_id': 3, 'limit': 2}],
              'user2':
                  [{'section_id': 2, 'limit': 0},
                   {'section_id': 3, 'limit': 2}],
              'user3':
                  [{'section_id': 2, 'limit': 0},
                   {'section_id': 3, 'limit': 2}]}

MESSAGE = 'You have reached your play limit for today.'
##/EDIT THESE SETTINGS ##

username = str(sys.argv[1])
sectionId = int(sys.argv[2])

TODAY = datetime.datetime.today().strftime('%Y-%m-%d')

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)


def get_history(username, section_id):
    # Get the Tautulli history.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'user': username,
               'section_id': section_id,
               'start_date': TODAY}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['recordsFiltered']
        return res_data

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))


def kill_session(user):
    for session in plex.sessions():
        # Check for users stream
        if session.usernames[0] in user:
            title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            print('{user} is watching {title} and they\'ve played too much today. Killing stream.'
                .format(user=user, title=title))
            session.stop(reason=MESSAGE)


for items in PLAY_LIMIT[username]:
    if sectionId == items['section_id']:
        section_id = items['section_id']
        limit = items['limit']

if get_history(username, section_id) > limit:
    print('User has reached play limit for today.')
    kill_session(username)
