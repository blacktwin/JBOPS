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
import platform
from uuid import getnode
import sys

## EDIT THESE SETTINGS ##
PLEX_HOST = ''
PLEX_PORT = 32400
PLEX_SSL = ''  # s or ''
PLEX_TOKEN = 'xxxxxxx'

REASON = 'Because....too many streams'

# 2nd stream information is passed
USER = sys.argv[1]
ADDRESS = sys.argv[2]

ignore_lst = ('')

if USER in ignore_lst:
    print(u"{} ignored.".format(USER))
    exit()


def fetch(path, t='GET'):
    url = 'http%s://%s:%s/' % (PLEX_SSL, PLEX_HOST, PLEX_PORT)

    headers = {'X-Plex-Token': PLEX_TOKEN,
               'Accept': 'application/json',
               'X-Plex-Provides': 'controller',
               'X-Plex-Platform': platform.uname()[0],
               'X-Plex-Platform-Version': platform.uname()[2],
               'X-Plex-Product': 'Plexpy script',
               'X-Plex-Version': '0.9.5',
               'X-Plex-Device': platform.platform(),
               'X-Plex-Client-Identifier': str(hex(getnode()))
               }

    try:
        if t == 'GET':
            r = requests.get(url + path, headers=headers, verify=False)
        elif t == 'POST':
            r = requests.post(url + path, headers=headers, verify=False)
        elif t == 'DELETE':
            r = requests.delete(url + path, headers=headers, verify=False)

        if r and len(r.content):  # incase it dont return anything

            return r.json()
        else:
            return r.content

    except Exception as e:
        print e

def kill_stream(sessionId, message):
    headers = {'X-Plex-Token': PLEX_TOKEN}
    params = {'sessionId': sessionId,
              'reason': message}
    requests.get('http://{}:{}/status/sessions/terminate'.format(PLEX_HOST, PLEX_PORT),
                     headers=headers, params=params)

response  = fetch('status/sessions')

sessions = []
for s in response['MediaContainer']['Video']:
    if s['User']['title'] == USER and s['Player']['address'] == ADDRESS:
        id = s['Session']['id']
        user = s['User']['title']
        title = (s['grandparentTitle'] + ' - ' if s['type'] == 'episode' else '') + s['title']
        sessions.append((id, user, title))

if len(sessions) == 1:
    for session in sessions:
        print(u"Killing {}'s second stream of {} for {}".format(session[1], session[2], REASON))
        kill_stream(session[0], REASON)
else:
    for session in sessions:
        print(u"Not killing {}'s second stream. Same IP".format(session[1]))
        break
