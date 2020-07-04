#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
from __future__ import print_function
from __future__ import unicode_literals
import argparse
import requests
from plexapi.server import PlexServer, CONFIG

PLEX_URL = ''
PLEX_TOKEN = ''
PLEX_URL = CONFIG.data['auth'].get('server_baseurl', PLEX_URL)
PLEX_TOKEN = CONFIG.data['auth'].get('server_token', PLEX_TOKEN)

# Allowed days/episodes to keep or delete
WATCHED_LST = [0, 1, 7]
UNWATCHED_LST = [0, 5, 3, 1, -3, -7, -30]

sess = requests.Session()
# Ignore verifying the SSL certificate
sess.verify = False  # '/path/to/certfile'
# If verify is set to a path to a directory,
# the directory must have been processed using the c_rehash utility supplied
# with OpenSSL.
if sess.verify is False:
    # Disable the warning that the request is insecure, we know that...
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

sections_lst = [x.title for x in plex.library.sections() if x.type == 'show']


def set_show(rating_key, action, number):

    path = '{}/prefs'.format(rating_key)
    try:
        params = {'X-Plex-Token': PLEX_TOKEN,
                  action: number
                  }

        r = requests.put(PLEX_URL + path, params=params, verify=False)
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
            set_show(show.key, setting, number)
