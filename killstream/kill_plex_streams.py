"""
Kill all streams
"""
import ConfigParser
import io
import requests
from plexapi.server import PlexServer

# Load the configuration file
with open("../config.ini") as f:
    real_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=False)
config.readfp(io.BytesIO(real_config))

PLEX_TOKEN=config.get('plex-data', 'PLEX_TOKEN')
PLEX_URL=config.get('plex-data', 'PLEX_URL')

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
