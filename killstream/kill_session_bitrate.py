"""
PlexPy Playback Start
"""

import requests
import platform
from uuid import getnode
import unicodedata

## EDIT THESE SETTINGS ##
PLEX_HOST = ''
PLEX_PORT = 32400
PLEX_SSL = ''  # s or ''
PLEX_TOKEN = 'xxxxxx'

ignore_lst = ('')


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
for video in response['MediaContainer']['Video']:
    media = video['Media'][0]
    id = video['Session']['id']
    user = video['User']['title']
    title = (video['grandparentTitle'] + ' - ' if video['type'] == 'episode' else '') + video['title']
    bitrate = media['bitrate']
    sessions.append((id, user, title, bitrate))

for session in sessions:
    if session[1] not in ignore_lst and int(session[3]) > 4000:
        message = "You are not allowed to stream above 4 Mbps."
        print("Killing {}'s stream of {} for {}".format(session[1], session[2], message))
        kill_stream(session[0], message)
