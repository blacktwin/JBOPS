# -*- coding: utf-8 -*-

'''
PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on pause
PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback Pause: wait_kill_pause_notify_main.py
PlexPy > Settings > Notifications > Script > Script Arguments:
        {session_key}

wait_kill_pause_notify_main.py & wait_kill_pause_notify_sub.py should be in the same directory.
wait_kill_pause_notify_main.py executes sub_script wait_kill_pause_notify_sub.py.

PlexPy will timeout wait_kill_pause_notify_main.py after 30 seconds (default)
    but wait_kill_pause_notify_sub.py will continue.

wait_kill_pause_notify_sub will check if the stream's session_id is still paused or if playing as restarted.
If playback is restarted then wait_kill_pause_notify_sub will stop and delete itself.
If stream remains paused then it will be killed and wait_kill_pause_notify_sub will stop.
Set TIMEOUT to max time before killing stream
Set INTERVAL to how often you want to check the stream status
'''

import os
import sys
import requests
import subprocess
from plexapi.server import PlexServer


## EDIT THESE SETTINGS ##
PLEX_TOKEN = ''
PLEX_URL = 'http://localhost:32400'
PLEXPY_APIKEY = ''  # Your PlexPy API key
PLEXPY_URL = 'http://localhost:8182/'  # Your PlexPy URL

TIMEOUT = '120'
INTERVAL = '20'

KILL_MESSAGE = 'This stream has ended due to being paused.'

USER_IGNORE = ('') # ('Username','User2')

SUBJECT_TEXT = "Killed Paused Transcoded Stream."
BODY_TEXT = "Killed {user}'s paused transcoded stream of {title}."

AGENT_ID = 10  # Notification agent ID for PlexPy
# Find Notification agent ID here:
# https://github.com/JonnyWong16/plexpy/blob/master/API.md#notify
# AGENT = '' to disable notification

sub_script = 'wait_kill_pause_notify_sub.py'
##/EDIT THESE SETTINGS ##

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

sessionKey = sys.argv[1]


def send_notification(subject_text, body_text):
    # Send the notification through PlexPy
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'notify',
               'agent_id': AGENT_ID,
               'subject': subject_text,
               'body': body_text}

    try:
        r = requests.post(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        if response['response']['result'] == 'success':
            sys.stdout.write("Successfully sent PlexPy notification.")
        else:
            raise Exception(response['response']['message'])
    except Exception as e:
        sys.stderr.write("PlexPy API 'notify' request failed: {0}.".format(e))
        return None


def check_session(sessionKey):
    for session in plex.sessions():
        if session.sessionKey == int(sessionKey):
            return session


def kill_stream(session, xtime, ntime):
    state = session.players[0].state
    username = session.usernames[0]
    title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title

    if state == 'paused' and xtime == ntime:
        session.stop(reason=KILL_MESSAGE)
        if AGENT_ID:
            send_notification(SUBJECT_TEXT, BODY_TEXT.format(user=username, title=title))
        return ntime
    elif state in ('playing', 'buffering'):
        sys.stdout.write("{user}'s stream of {title} is now {state}".format(user=username, title=title,
                                                                            state=state))
        return None
    else:
        return xtime


if __name__ == '__main__':

    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    fileDir = os.path.dirname(os.path.realpath(__file__))
    sub_path = os.path.join(fileDir, sub_script)

    for session in plex.sessions():
        if session.sessionKey == int(sessionKey) and session.usernames[0] not in USER_IGNORE:
            subprocess.Popen([sys.executable, sub_path, sessionKey, TIMEOUT, INTERVAL],
                             startupinfo=startupinfo)
