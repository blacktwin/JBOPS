"""

Kill Plex paused video transcoding streams and receive notification.

PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback pause

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback Pause: kill_trans_pause.py

"""

import ConfigParser
import io
import sys
import requests
from plexapi.server import PlexServer

# Load the configuration file
with open("../config.ini") as f:
    real_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=False)
config.readfp(io.BytesIO(real_config))

PLEX_TOKEN=config.get('plex-data', 'PLEX_TOKEN')
PLEX_URL=config.get('plex-data', 'PLEX_URL')
PLEXPY_APIKEY=config.get('plexpy-data', 'PLEXPY_APIKEY')
PLEXPY_URL=config.get('plexpy-data', 'PLEXPY_URL')

KILL_MESSAGE = 'This stream has ended due to being paused and transcoding.'

USER_IGNORE = ('') # ('Username','User2')

SUBJECT_TEXT = "Killed Paused Transcoded Stream."
BODY_TEXT = "Killed {user}'s paused transcoded stream of {title}."

AGENT_ID = 14  # Notification agent ID for PlexPy
# Find Notification agent ID here:
# https://github.com/JonnyWong16/plexpy/blob/master/API.md#notify

##/EDIT THESE SETTINGS ##

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

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


for session in plex.sessions():
    username = session.usernames[0]
    state = session.players[0].state
    video_decision = session.transcodeSessions[0].videoDecision
    title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title

    if video_decision == 'transcode' and state == 'paused' and username not in USER_IGNORE:
        sys.stdout.write("Killing {user}'s stream of {title}.".format(user=username, title=title))
        session.stop(reason=KILL_MESSAGE)
        send_notification(SUBJECT_TEXT, BODY_TEXT.format(user=username, title=title))
