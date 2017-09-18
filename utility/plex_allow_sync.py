"""
Allow syncing for users

"""

import requests
from plexapi.server import PlexServer

PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxx'
plex = PlexServer(PLEX_URL, PLEX_TOKEN)

USER_IGNORE = ['username']

user_lst = [str(user.id) for user in plex.myPlexAccount().users() if user.title not in USER_IGNORE]

payload = {'X-Plex-Token': PLEX_TOKEN,
           'allowSync': 0}

for user_id in user_lst:
    r = requests.put('http://plex.tv/api/friends/' + user_id, params=payload)
    print(r.status_code)
