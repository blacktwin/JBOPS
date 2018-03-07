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

Example:
python plex_api_show_settings.py --libraries "TV Shows" --watched 7
   - Delete episodes after watching After 1 week

python plex_api_show_settings.py --libraries "TV Shows" --unwatched -7
   - Keep Episodesfrom the past 7 days
"""
import argparse
import requests
from plexapi.server import PlexServer


PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxxx'

# Allowed days/episodes to keep or delete
WATCHED_LST = [0, 1, 7]
UNWATCHED_LST = [0, 5, 3, 1, -3, -7,-30]

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

sections_lst = [x.title for x in plex.library.sections() if x.type == 'show']


def set(rating_key, action, number):

    path = '{}/prefs'.format(rating_key)
    try:
        params = {'X-Plex-Token': PLEX_TOKEN,
                   action: number
                   }

        r = requests.put(PLEX_URL + path,  params=params, verify=False)
        print(r.url)
    except Exception as e:
        print('Error: {}'.format(e))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Change show deletion settings by library.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--libraries', nargs='+', default=False, choices=sections_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s)')
    parser.add_argument('--watched', nargs='?', default=False, choices=WATCHED_LST, metavar='',
                        help='Keep: Set the maximum number of unwatched episodes to keep for the show. \n'
                             '(choices: %(choices)s)')
    parser.add_argument('--unwatched', nargs='?', default=False, choices=UNWATCHED_LST, metavar='',
                        help='Delete episodes after watching: '
                             'Choose how quickly episodes are removed after the server admin has watched them. \n'
                             '(choices: %(choices)s)')

    opts = parser.parse_args()

    if opts.watched:
        setting = 'autoDeletionItemPolicyWatchedLibrary'
        number = opts.watched
    if opts.unwatched:
        setting = 'autoDeletionItemPolicyUnwatchedLibrary'
        number = opts.unwatched

    for libary in opts.libraries:
        shows = plex.library.section(libary).all()

        for show in shows:
            set(show.key, setting, number)
