"""
Change show deletion settings by library.

Keep: (section)
autoDeletionItemPolicyUnwatchedLibrary
5   - keep 5 episode
-30 - keep episodes from last 30 days
0   - keep all episodes

[0, 5, 3, 1, -3, -7,-30]

Delete episodes after watching: (section)
autoDeletionItemPolicyWatchedLibrary=7

[0, 1, 7]


"""
import requests
from plexapi.server import PlexServer


PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxx'

LIBRARY = 'TV Shows'

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)


def set(rating_key, action, n):
    if action == 'delete':
        setting = 'autoDeletionItemPolicyWatchedLibrary'
        if n in [0, 1, 7]:
            number = n
    elif action == 'keep':
        setting = 'autoDeletionItemPolicyUnwatchedLibrary'
        if n in [0, 5, 3, 1, -3, -7,-30]:
            number = n

    url = PLEX_URL
    path = '{}/prefs'.format(rating_key)
    try:
        params = {'X-Plex-Token': PLEX_TOKEN,
                   setting: number
                   }

        r = requests.put(url + path,  params=params, verify=False)
        print(r.url)
    except Exception as e:
        print('Error: {}'.format(e))


shows = plex.library.section(LIBRARY).all()

for show in shows:
    set(show.key, 'keep', -7)
