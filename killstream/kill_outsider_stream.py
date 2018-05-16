"""
Kill stream of user if they are accessing Plex from outside network

PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: kill_outsider_stream.py

PlexPy > Settings > Notifications > Script > Script Arguments
        {username}
"""

import requests
import ConfigParser
import io
import os.path
from plexapi.server import PlexServer
import sys

## EDIT THESE SETTINGS IF NOT USING THE CONFIG ##
PLEX_TOKEN = 'xxxxxx'
PLEX_URL = 'http://localhost:32400'

## DO NOT EDIT
config_exists = os.path.exists("../config.ini")
if config_exists:
    # Load the configuration file
    with open("../config.ini") as f:
        real_config = f.read()
        config = ConfigParser.RawConfigParser(allow_no_value=False)
        config.readfp(io.BytesIO(real_config))

        PLEX_TOKEN=config.get('plex-data', 'PLEX_TOKEN')
        PLEX_URL=config.get('plex-data', 'PLEX_URL')
##/DO NOT EDIT

MESSAGE = 'Accessing Plex from outside network'

ignore_lst = ('')
## EDIT THESE SETTINGS ##

USERNAME = sys.argv[1]

if USERNAME in ignore_lst:
    print(u"{} ignored.".format(USERNAME))
    exit()

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

def kill_session(user):
    for session in plex.sessions():
        # Check for users stream
        if session.usernames[0] == user and session.players[0].local is False:
            title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            print('{user} is watching {title} and they might be asleep.'.format(user=user, title=title))
            session.stop(reason=MESSAGE)

kill_session(USERNAME)
