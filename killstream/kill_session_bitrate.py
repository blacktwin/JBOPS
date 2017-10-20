"""
Kill stream if bitrate is > BITRATE_LIMIT

PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: kill_session_bitrate.py

"""

import requests
from plexapi.server import PlexServer

## EDIT THESE SETTINGS ##
PLEX_TOKEN = 'xxxxx'
PLEX_URL = 'http://localhost:32400'

MESSAGE = "You are not allowed to stream above 4 Mbps."

ignore_lst = ('')
##/EDIT THESE SETTINGS ##

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

def kill_session():
    for session in plex.sessions():
        bitrate = session.media[0].parts[0].streams[0].bitrate
        user = session.usernames[0]
        if user not in ignore_lst and int(bitrate) > 4000:
            title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            print('{user} is watching {title} and they might be asleep.'.format(user=user, title=title))
            session.stop(reason=MESSAGE)

kill_session()
