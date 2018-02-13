'''
fetch function from https://gist.github.com/Hellowlol/ee47b6534410b1880e19
PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on pause

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback Pause: create_wait_kill_all.py

PlexPy > Settings > Notifications > Script > Script Arguments:
        {session_key}


create_wait_kill_all.py creates a new file with the session_id (sub_script) as it's name.
PlexPy will timeout create_wait_kill_all.py after 30 seconds (default) but sub_script.py will continue.
sub_script will check if the stream's session_id is still pause or if playing as restarted.
If playback is restarted then sub_script will stop and delete itself.
If stream remains paused then it will be killed and sub_script will stop and delete itself.

Set TIMEOUT to max time before killing stream
Set INTERVAL to how often you want to check the stream status
'''

import os
import platform
import subprocess
import ConfigParser
import io
import sys
from uuid import getnode
import unicodedata

import requests


# Load the configuration file
with open("../config.ini") as f:
    real_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=False)
config.readfp(io.BytesIO(real_config))

PLEX_HOST=config.get('plex-data', 'PLEX_HOST')
PLEX_PORT=config.get('plex-data', 'PLEX_PORT')
PLEX_TOKEN=config.get('plex-data', 'PLEX_TOKEN')
PLEX_URL=config.get('plex-data', 'PLEX_URL')
PLEX_SSL=config.get('plex-data', 'PLEX_SSL')

PLEXPY_APIKEY=config.get('plexpy-data', 'PLEXPY_APIKEY')
PLEXPY_URL=config.get('plexpy-data', 'PLEXPY_URL')


TIMEOUT = 120
INTERVAL = 20

REASON = 'Because....'
ignore_lst = ('test')


class Activity(object):
    def __init__(self, data=None):
        d = data or {}
        self.video_decision = d['video_decision']
        self.state = d['state']
        self.session_key = d['session_key']


def get_get_activity():
    # Get the user IP list from PlexPy
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_activity'}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']['sessions']
        return [Activity(data=d) for d in res_data]

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_get_activity' request failed: {0}.".format(e))


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


def kill_stream(sessionId, message, xtime, ntime, user, title, sessionKey):
    headers = {'X-Plex-Token': PLEX_TOKEN}
    params = {'sessionId': sessionId,
              'reason': message}

    activity = get_get_activity()

    for a in activity:
        if a.session_key == sessionKey:
            if a.state == 'paused' and xtime == ntime:
                sys.stdout.write("Killing {user}'s paused stream of {title}".format(user=user, title=title))
                requests.get('http{}://{}:{}/status/sessions/terminate'.format(PLEX_SSL, PLEX_HOST, PLEX_PORT),
                             headers=headers, params=params)
                return ntime
            elif a.state in ('playing', 'buffering'):
                sys.stdout.write("{user}'s stream of {title} is now {state}".format(user=user, title=title,
                                                                                    state=a.state))
                return None
            else:
                return xtime


def find_sessionID(response):

    sessions = []
    for video in response['MediaContainer']['Video']:
        if video['sessionKey'] == sys.argv[1]:
            sess_id = video['Session']['id']
            user = video['User']['title']
            sess_key = video['sessionKey']
            title = (video['grandparentTitle'] + ' - ' if video['type'] == 'episode' else '') + video['title']
            title = unicodedata.normalize('NFKD', title).encode('ascii','ignore')
            sessions.append((sess_id, user, title, sess_key))
        else:
            pass

    for session in sessions:
        if session[1] not in ignore_lst:
            return session
        else:
            print("{}'s stream of {} is ignored.".format(session[1], session[2]))
            return None


if __name__ == '__main__':

    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    response = fetch('status/sessions')
    fileDir = fileDir = os.path.dirname(os.path.realpath(__file__))

    try:
        if find_sessionID(response):
            stream_info = find_sessionID(response)
            file_name = "{}.py".format(stream_info[0])
            full_path = os.path.join(fileDir, file_name)
            file = 'from time import sleep\n' \
                   'import sys, os\n' \
                   'from {script} import kill_stream \n' \
                   'message = "{REASON}"\n' \
                   'sessionID =  os.path.basename(sys.argv[0])[:-3]\n' \
                   'x = 0\n' \
                   'n = {ntime}\n' \
                   'try:\n' \
                   '    while x < n and x is not None:\n' \
                   '        sleep({xtime})\n' \
                   '        x += kill_stream(sessionID, message, {xtime}, n, "{user}", "{title}", "{sess_key}")\n' \
                   '    kill_stream(sessionID, message, {ntime}, n, "{user}", "{title}", "{sess_key}")\n' \
                   '    os.remove(sys.argv[0])\n' \
                   'except TypeError as e:\n' \
                   '    os.remove(sys.argv[0])'.format(script=os.path.basename(__file__)[:-3],
                                                   ntime=TIMEOUT, xtime=INTERVAL, REASON=REASON,
                                                   user=stream_info[1], title=stream_info[2], sess_key=stream_info[3])

            with open(full_path, "w+") as output:
                output.write(file)

            subprocess.Popen([sys.executable, full_path], startupinfo=startupinfo)
            exit(0)

    except TypeError as e:
        print(e)
        pass
