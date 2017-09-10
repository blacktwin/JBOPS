'''
If server admin stream is experiencing buffering and there are concurrent transcode streams from
another user, kill concurrent transcode stream that has the lowest percent complete. Message in
kill stream will list why it was killed ('Server Admin's stream take priority and this user has X
concurrent streams'). Message will also include an approximation of when the other concurrent stream
will finish, stream that is closest to finish will be used.

PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on buffer warning

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Buffer Warnings: kill_else_if_buffering.py

'''

import requests
import platform
from uuid import getnode
from operator import itemgetter
import unicodedata

## EDIT THESE SETTINGS ##
PLEX_HOST = ''
PLEX_PORT = 32400
PLEX_SSL = ''  # s or ''
PLEX_TOKEN = 'xxxxxx'
DEFAULT_REASON = 'Server Admin\'s stream takes priority and {user}(you) has {x} concurrent streams.' \
                 ' {user}\'s stream of {video} is {time}% complete. Should be finished in {comp} minutes. ' \
                 'Try again then.'

ADMIN_USER = ('Admin') # additional usernames can be added ('Admin', 'user2')
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

def add_to_dictlist(d, key, val):
    if key not in d:
        d[key] = [val]
    else:
        d[key].append(val)


if __name__ == '__main__':
    response  = fetch('status/sessions')

    user_dict = {}
    sessions = []

    if 'Video' in response['MediaContainer']:
        for video in response['MediaContainer']['Video']:
            try:
                if video['TranscodeSession']['videoDecision'] == 'transcode' and video['User']['title'] not in ADMIN_USER:
                    sess_id = video['Session']['id']
                    user = video['User']['title']
                    percent_comp =  int((float(video['viewOffset']) / float(video['duration'])) * 100)
                    time_to_comp = int(int(video['duration']) - int(video['viewOffset'])) / 1000 / 60
                    title = video['title']
                    title = unicodedata.normalize('NFKD', title).encode('ascii','ignore')
                    add_to_dictlist(user_dict, user, [sess_id, percent_comp, title, user, time_to_comp])

            except KeyError:
                print('{} has a direct stream to ignore.'.format(video['User']['title']))

    # Remove users with only 1 stream. Targeting users with multiple concurrent streams
    filtered_dict = {key: value for key, value in user_dict.items()
                 if len(value) is not 1}

    # Find who to kill and who will be finishing first.
    for session in filtered_dict.values():
        to_kill = min(session, key=itemgetter(1))
        to_finish = max(session, key=itemgetter(1))

    MESSAGE = DEFAULT_REASON.format(user=to_finish[3], x=len(filtered_dict.values()[0]),
                                    video=to_finish[2], time=to_finish[1], comp=to_finish[4])

    print(MESSAGE)
    kill_stream(to_kill[0], MESSAGE)
