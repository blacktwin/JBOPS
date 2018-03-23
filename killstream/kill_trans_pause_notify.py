"""

Kill Plex paused video transcoding streams and receive notification.

Tautulli > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback pause

Tautulli > Settings > Notification Agents > Scripts > Gear icon:
        Playback Pause: kill_trans_pause.py

"""

import sys
import requests
from plexapi.server import PlexServer


## EDIT THESE SETTINGS ##
PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxxx'
TAUTULLI_APIKEY = 'xxxxx'  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL

KILL_MESSAGE = 'This stream has ended due to being paused and transcoding.'

USER_IGNORE = ('') # ('Username','User2')

SUBJECT_TEXT = "Killed Paused Transcoded Stream."
BODY_TEXT = "Killed {user}'s paused transcoded stream of {title}."

NOTIFIER_ID = 14  # Notification agent ID for Tautulli
# Find Notification agent ID here:
# Tautulli Settings -> NOTIFICATION AGENTS -> :bell: Agent (NotifierID - {Description)

##/EDIT THESE SETTINGS ##

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

def send_notification(subject_text, body_text):
    # Send the notification through Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'notify',
               'notifier_id': NOTIFIER_ID,
               'subject': subject_text,
               'body': body_text}

    try:
        r = requests.post(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        if response['response']['result'] == 'success':
            sys.stdout.write("Successfully sent Tautulli notification.")
        else:
            raise Exception(response['response']['message'])
    except Exception as e:
        sys.stderr.write("Tautulli API 'notify' request failed: {0}.".format(e))
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
