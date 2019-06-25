#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Removes Shows from On Deck.

Author: Blacktwin
Requires: requests, plexapi

 Example:
     python off_deck.py --action deck --user Steve
        - Display what shows are on Steve's On Deck

     python off_deck.py --action deck --shows "The Simpsons" Seinfeld
        - The Simpsons and Seinfeld will be removed from On Deck

     python off_deck.py --action deck --shows "The Simpsons" Seinfeld --user Steve
        - The Simpsons and Seinfeld will be removed from Steve's On Deck

     python off_deck.py --action deck --playlist "Favorite Shows!"
        - Any Show found in Favorite Shows playlist will be remove
        from On Deck

     python off_deck.py --action watch --user Steve
        - Display what shows are on Steve's Continue Watching

     python off_deck.py --action watch --shows "The Simpsons" Seinfeld
        - The Simpsons and Seinfeld will be removed from Continue Watching

     python off_deck.py --action watch --shows "The Simpsons" Seinfeld --user Steve
        - The Simpsons and Seinfeld will be removed from Steve's Continue Watching

     python off_deck.py --action watch --playlist "Favorite Shows!"
        - Any Show found in Favorite Shows playlist will be remove
        from Continue Watching

!!!NOTICE!!!

 * This script should be used for Shows that you have already watched and
don't want showing up on your On Deck.

 * For episodes of show already watched the view count will be reset back to it
original.

 * For episodes of show not watched the view count will be set to 1.

"""

import requests
import argparse
import datetime
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


def actions():
    """
    deck - Items that are On Deck
    watch - Items that are Continue Watching
    """
    return ['deck', 'watch']


def get_con_watch(server, off_deck=None):
    """

    Parameters
    ----------
    server : class
        User's server to pull On Deck list
    Returns
    -------
    dict
        Show, episodes, and episodes view count

    """
    con_watch = []
    for item in server.library.onDeck():
        if off_deck and item.type == 'episode' and item.viewOffset > 0:
            if item.grandparentTitle in off_deck:
                print('Removing {}: S{:02}E{:02} {} from Continue Watching '
                      'by marking watched.'.format(
                          item.grandparentTitle.encode('UTF-8'),
                          int(item.parentIndex), int(item.index),
                          item.title.encode('UTF-8')))
                item.markWatched()
        else:
            if item.type == 'episode' and item.viewOffset > 0:
                con_watch.append(item)

    if con_watch:
        print('The following shows are marked Continue Watching:')
        for item in con_watch:
            offset = datetime.timedelta(milliseconds=item.viewOffset)
            print('{}: S{:02}E{:02} {} ({})'.format(
                item.grandparentTitle.encode('UTF-8'),
                int(item.parentIndex), int(item.index),
                item.title.encode('UTF-8'), offset))


def get_on_deck(server, off_deck=None):
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
    on_deck = []
    for item in server.library.onDeck():
        if off_deck and item.type == 'episode' and item.viewOffset == 0:
            if item.grandparentTitle in off_deck:
                grandparent = server.fetchItem(item.grandparentRatingKey)
                watched_statuses['grandparent'] = grandparent
                watched_statuses['episodes'] = []
                for episode in grandparent.episodes():
                    watched_statuses['episodes'].append({
                        'object': episode,
                        'viewCount': episode.viewCount})
        else:
            if item.type == 'episode':
                on_deck.append(item)

    if on_deck:
        watched_statuses['on_deck'] = on_deck
    return watched_statuses


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Remove items from On Deck.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--shows', nargs='+',
                        help='Shows to be removed from On Deck.')
    parser.add_argument('--user', nargs='?',
                        help='User whose On Deck will be modified.')
    parser.add_argument('--playlist', nargs='?',
                        help='Shows in playlist to be removed from On Deck')
    parser.add_argument('--action', required=True, choices=actions(),
                        help='Action selector.'
                             '{}'.format(actions.__doc__))

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
        to_remove = [x.grandparentTitle for x in plex_server.playlist(opts.playlist).items()]

    if opts.action == 'deck':
        if not to_remove:
            print('The following shows are On Deck...')
            on_deck = get_on_deck(plex_server)['on_deck']
            for item in on_deck:
                print('{}: S{:02}E{:02} {}'.format(
                    item.grandparentTitle.encode('UTF-8'),
                    int(item.parentIndex), int(item.index),
                    item.title.encode('UTF-8')))

        else:
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

    elif opts.action == 'watch':
        print('Finding shows marked Continue Watching...')
        get_con_watch(plex_server, to_remove)
