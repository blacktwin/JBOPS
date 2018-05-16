"""
Kill Plex transcoding streams from specific libraries

PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: kill_trans_library.py

PlexPy > Settings > Notifications > Script > Script Arguments:
        {section_id} {session_key}

"""
import ConfigParser
import io
import os.path
import sys
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

TARGET_LIBRARIES = ['1', '2'] # Library IDs

DEFAULT_REASON = 'Stream terminated due to video transcoding of {} content. ' \
                 'Please set your device to use "Original" quality.'.format(', '.join(TARGET_LIBRARIES))

# Find platforms that have history in PlexPy in Play count by platform and stream type Graph
DEVICES = {'Android': 'Andriod message',
           'Chrome': 'Chrome message',
           'Plex Media Player': 'PMP message',
           'Chromecast': 'Chromecast message'}

USER_IGNORE = ('') # ('Username','User2')

PLEXPY_LOG = 'Killing {user}\'s stream of {title} due to video transcoding content from section {section}.'
##

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

if __name__ == '__main__':

    lib_id = sys.argv[1]
    session_key = int(sys.argv[2])

    for session in plex.sessions():
        username = session.usernames[0]
        media_type = session.type
        section_id = session.librarySectionID
        if username not in USER_IGNORE and media_type != 'track' and lib_id == section_id and session.sessionKey == session_key:
            title = session.title
            if session.transcodeSessions:
                trans_dec = session.transcodeSessions[0].videoDecision
                if trans_dec == 'transcode':
                    reason = DEVICES.get(session.players[0].platform, DEFAULT_REASON)
                    print(PLEXPY_LOG.format(user=username, title=title, section=section_id))
                    session.stop(reason=reason)
