"""
Kill Plex transcoding streams only. Checks original quality.

PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: kill_trans_quality.py

PlexPy > Settings > Notifications > Script > Script Arguments:
        {rating_key}

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

TARGET_QUALITY = ['1080', '4k']

DEFAULT_REASON = 'Stream terminated due to video transcoding of {} content. ' \
                 'Please set your device to use "Original" quality.'.format(', '.join(TARGET_QUALITY))

DEVICES = {'Android': 'Andriod message',
           'Chrome': 'Chrome message',
           'Plex Media Player': 'PMP message',
           'Chromecast': 'Chromecast message'}

USER_IGNORE = ('') # ('Username','User2')

PLEXPY_LOG = 'Killing {user}\'s stream of {title} due to video transcoding of {original} content'
##

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

if __name__ == '__main__':

    rating_key = sys.argv[1]
    item = plex.fetchItem(int(rating_key))
    orig_quality = item.media[0].videoResolution
    # print(orig_quality)

    for session in plex.sessions():
        username = session.usernames[0]
        media_type = session.type
        if username not in USER_IGNORE and media_type != 'track':
            title = session.title
            sess_rating = session.key.split('/')[3]
            trans_dec = session.transcodeSessions[0].videoDecision
            if sess_rating == str(rating_key) and orig_quality in TARGET_QUALITY and trans_dec == 'transcode':
                reason = DEVICES.get(session.players[0].platform, DEFAULT_REASON)
                print(PLEXPY_LOG.format(user=username, title=title,original=orig_quality))
                session.stop(reason=reason)
