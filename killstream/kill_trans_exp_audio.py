"""

Kill Plex video transcoding streams only. All audio streams are left alone.

PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: kill_trans_exp_audio.py

Create custom messages for platforms.
		
"""
import requests
import platform
from uuid import getnode


## EDIT THESE SETTINGS ##
PLEX_HOST = ''
PLEX_PORT = 32400
PLEX_SSL = ''  # s or ''
PLEX_TOKEN = 'xxxxx'
DEFAULT_REASON = 'This stream has ended due to requiring video transcoding. ' \
         'Please raise your Remote Quality to Original to play this content.'

# Find platforms that have history in PlexPy in Play count by platform and stream type Graph
DEVICES = {'Android': 'Andriod message',
           'Chrome': 'Chrome message',
           'Plex Media Player': 'PMP message',
           'Chromecast': 'Chromecast message'}

USER_IGNORE = ('') # ('Username','User2')
##

def fetch(path, t='GET'):
    url = 'http{}://{}:{}/'.format(PLEX_SSL, PLEX_HOST, PLEX_PORT)

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
    requests.get('http{}://{}:{}/status/sessions/terminate'.format(PLEX_SSL, PLEX_HOST, PLEX_PORT),
                 headers=headers, params=params)

if __name__ == '__main__':
    response  = fetch('status/sessions')

    if 'Video' in response['MediaContainer']:
        for video in response['MediaContainer']['Video']:
            if video['TranscodeSession']['videoDecision'] == 'transcode' and video['User']['title'] not in USER_IGNORE:
                MESSAGE = DEVICES.get(video['Player']['platform'], DEFAULT_REASON)
                print("Killing {}'s stream for transcoding video".format(video['User']['title']))
                kill_stream(video['Session']['id'], MESSAGE)
    elif 'Track' in response['MediaContainer']:
        for track in response['MediaContainer']['Track']:
            print("{} is streaming audio, let them pass!".format(track['User']['title']))
            exit()
    else:
        exit()
