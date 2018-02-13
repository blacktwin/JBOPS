"""
If user has 2* or more concurrent streams kill all user's streams


*PlexPy > Settings > Notification> User Concurrent Stream Threshold
    The number of concurrent streams by a single user for PlexPy to trigger a notification. Minimum 2.

PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on user concurrent streams

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback User Concurrent Streams: kill_more_than.py

PlexPy > Settings > Notifications > Script > Script Arguments
        {user}
"""

import requests
import ConfigParser
import io
import sys
from plexapi.server import PlexServer

# Load the configuration file
with open("../config.ini") as f:
    real_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=False)
config.readfp(io.BytesIO(real_config))

PLEX_TOKEN=config.get('plex-data', 'PLEX_TOKEN')
PLEX_URL=config.get('plex-data', 'PLEX_URL')

MESSAGE = 'Because....too many streams'
ignore_lst = ('')
## EDIT THESE SETTINGS ##

# 2nd stream information is passed
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
        if session.usernames[0] in user:
            print('Killing all of {user}\'s streams. Too many streams'.format(user=user))
            session.stop(reason=MESSAGE)

kill_session(USERNAME)
