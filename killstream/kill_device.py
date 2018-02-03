"""
Kill Plex streams based on device.

PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start

PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: kill_device.py

"""
import requests
import ConfigParser
import io
from plexapi.server import PlexServer

# Load the configuration file
with open("../config.ini") as f:
    real_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=False)
config.readfp(io.BytesIO(real_config))

PLEX_TOKEN=config.get('plex-data', 'PLEX_TOKEN')
PLEX_URL=config.get('plex-data', 'PLEX_URL')


DEFAULT_REASON = 'This stream has ended due to your device type.'

# Find platforms that have history in PlexPy in Play count by platform and stream type Graph
DEVICES = {'Android': 'Andriod message',
           'Chrome': 'Chrome message',
           'Plex Media Player': 'PMP message',
           'Chromecast': 'Chromecast message'}

USER_IGNORE = ('') # ('Username','User2')
##/EDIT THESE SETTINGS ##

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

def kill_session():

    for session in plex.sessions():
        user = session.usernames[0]
        if user in USER_IGNORE:
            print('Ignoring {}\'s stream from platform check.'.format(user))
            exit()

        platform = session.players[0].platform
        if DEVICES[platform]:
            MESSAGE = DEVICES.get(platform, DEFAULT_REASON)
            print('Killing {user}\'s stream on {plat}.'.format(user=user, plat=platform))
            session.stop(reason=MESSAGE)
        else:
            print('{user}\'s stream on {plat} is allowed to play.'.format(user=user, plat=platform))

if __name__ == '__main__':
    kill_session()
