"""
Allow syncing for users

"""

import requests
from plexapi.server import PlexServer

PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxx'
plex = PlexServer(PLEX_URL, PLEX_TOKEN)

USER_IGNORE = ['username']

headers = {'X-Plex-Token': PLEX_TOKEN}
payload = {'allowSync': 1}  # 1 = Allow, 0 = Not Allow

for user in plex.myPlexAccount().users():
    if user.title not in USER_IGNORE:
        r = requests.put('http://plex.tv/api/friends/{}'.format(user.id), headers=headers, params=payload)
