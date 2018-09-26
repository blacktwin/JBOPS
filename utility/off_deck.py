#!/usr/bin/env python
"""
Description: Removes Shows from On Deck
Author: Blacktwin
Requires: requests, plexapi

 Example:
     python off_deck.py --shows "The Simpsons" Seinfeld
        - The Simpsons and Seinfeld will be removed from On Deck

     python off_deck.py --shows "The Simpsons" Seinfeld --user Steve
        - The Simpsons and Seinfeld will be removed from Steve's On Deck

     python off_deck.py --playlist "Favorite Shows!"
        - Any Show found in Favorite Shows playlist will be remove
        from On Deck

!!!NOTICE!!!

 * This script should be used for Shows that you have already watched and
don't want showing up on your On Deck.

 * For episodes of show already watched the view count will be reset back to it
original.

 * For episodes of show not watched the view count will be set to 1.

"""

import requests
import argparse
from plexapi.server import PlexServer, CONFIG

PLEX_URL = ''
PLEX_TOKEN = ''

if not PLEX_URL:
    PLEX_URL = CONFIG.data['auth'].get('server_baseurl', '')

if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token', '')

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
account = plex.myPlexAccount()


def get_on_deck(server, off_deck):
    """

    Parameters
    ----------
    server : class
        User's server to pull On Deck list
    off_deck : list
        List of Shows to remove from On Deck

    Returns
    -------
    dict
        Show, episodes, and episodes view count

    """
    watched_statuses = {}
    for item in server.library.onDeck():
        if item.type == 'episode' and item.grandparentTitle in off_deck:
            grandparent = server.fetchItem(item.grandparentRatingKey)
            watched_statuses['grandparent'] = grandparent
            watched_statuses['episodes'] = []
            for episode in grandparent.episodes():
                watched_statuses['episodes'].append({'object': episode,
                                'viewCount': episode.viewCount})
    return watched_statuses


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Remove items from On Deck.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--shows', nargs='+',
                        help='Shows to be removed from On Deck.')
    parser.add_argument('--user', nargs='?',
                        help='User whose On Deck will be modified.')
    parser.add_argument('--playlist', nargs='?',
                        help='Items in playlist to be removed from On Deck')

    opts = parser.parse_args()

    ep_list = []
    to_remove = ''

    if opts.user:
        user_acct = account.user(opts.user)
        plex_server = PlexServer(PLEX_URL, user_acct.get_token(plex.machineIdentifier))
    else:
        plex_server = plex

    if opts.shows and not opts.playlist:
        to_remove = opts.shows
    elif not opts.shows and opts.playlist:
        to_remove = [x.title for x in plex_server.playlist(opts.playlist).items()]

    if not to_remove:
        print('Nothing to remove...')
        exit()

    print('Finding listed shows On Deck...')
    while True:
        off_deck = get_on_deck(plex_server, to_remove)
        if off_deck:
            ep_list += off_deck['episodes']
            print('Marking {} Unwatched'.format(off_deck['grandparent']
                                                .title.encode('UTF-8')))
            off_deck['grandparent'].markUnwatched()
        else:
            break

    print('Resetting watch counts...')
    for item in ep_list:
        print('Resetting view count for {}: S{:02}E{:02} {}'.format(
            item['object'].grandparentTitle.encode('UTF-8'),
            int(item['object'].parentIndex), int(item['object'].index),
            item['object'].title.encode('UTF-8')))
        # if viewCount was 0 then make 1 so as not to return to On Deck.
        for _ in range(item['viewCount'] if item['viewCount'] != 0 else 1):
            item['object'].markWatched()