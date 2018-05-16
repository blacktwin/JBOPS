"""
Kill all streams
"""
import ConfigParser
import io
import os.path
import requests
from plexapi.server import PlexServer

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

MESSAGE = 'Because....'
ignore_lst = ('')
##/EDIT THESE SETTINGS ##

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

def kill_session():
    for session in plex.sessions():
        user = session.usernames[0]
        if user not in ignore_lst:
            title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            print("Killing {}'s stream of {} for {}".format(user, title, MESSAGE))
            session.stop(reason=MESSAGE)

kill_session()
