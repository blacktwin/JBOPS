"""
Kill Plex transcoding streams from specific libraries

PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: kill_trans_library.py

PlexPy > Settings > Notifications > Script > Script Arguments:
        {section_id}

"""
import sys
import requests
from plexapi.server import PlexServer

## EDIT THESE SETTINGS ##
PLEX_TOKEN = 'xxxxx'
PLEX_URL = 'http://localhost:32400'

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

    for session in plex.sessions():
        username = session.usernames[0]
        media_type = session.type
        if username not in USER_IGNORE or media_type != 'track':
            title = session.title
            section_id = session.librarySectionID
            trans_dec = session.transcodeSessions[0].videoDecision
            if lib_id == section_id and trans_dec == 'transcode':
                reason = DEVICES.get(session.players[0].platform, DEFAULT_REASON)
                print(PLEXPY_LOG.format(user=username, title=title, section=section_id))
                session.stop(reason=reason)
