"""
Kill Plex paused video transcoding streams.

PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback pause

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback Pause: kill_trans_pause.py

PlexPy > Settings > Notifications > Script > Script Arguments:
        {session_key}

"""

import requests
import sys
from plexapi.server import PlexServer

## EDIT THESE SETTINGS ##
PLEX_TOKEN = 'xxxx'
PLEX_URL = 'http://localhost:32400'

MESSAGE = "You've paused a transcoded stream."

ignore_lst = ('')
##/EDIT THESE SETTINGS ##

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

def kill_session(sess_key):
    for session in plex.sessions():
        user = session.usernames[0]
        if user in ignore_lst:
            print('Ignoring {}\'s paused transcode stream.'.format(user))
            exit()
        state = session.players[0].state
        if session.transcodeSessions:
            trans_dec = session.transcodeSessions[0].videoDecision
            if session.sessionKey == sess_key and state == 'paused' and trans_dec == 'transcode':
                title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
                print('Killing {user}\'s stream for pausing a transcode stream of {title}.'.format(user=user, title=title))
                session.stop(reason=MESSAGE)


if __name__ == '__main__':
    session_key = int(sys.argv[1])
    kill_session(session_key)
