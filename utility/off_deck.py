#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Removes Shows from Continue Watching.

Author: Blacktwin
Requires: requests, plexapi

 Example:
     python off_deck.py
        - Display what shows are on admin's Continue Watching
        
     python off_deck.py --user Steve
        - Display what shows are on Steve's Continue Watching

     python off_deck.py  --shows "The Simpsons" Seinfeld
        - The Simpsons and Seinfeld Episodes will be removed from admin's Continue Watching

     python off_deck.py  --user Steve --shows "The Simpsons" Seinfeld
        - The Simpsons and Seinfeld Episodes will be removed from Steve's Continue Watching

     python off_deck.py --playlists "Favorite Shows!"
        - Any Episode found in admin's "Favorite Shows" playlist will be remove from Continue Watching
    
     python off_deck.py --user Steve --playlists "Favorite Shows!" SleepMix
        - Any Episode found in Steve's "Favorite Shows" or SleepMix playlist will be remove from Continue Watching

"""
from __future__ import print_function
from __future__ import unicode_literals

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


def remove_from_cw(server, ratingKey):
    key = '/actions/removeFromContinueWatching?ratingKey=%s&' % ratingKey
    server.query(key, method=server._session.put)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Remove items from Continue Watching.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--shows', nargs='+',
                        help='Shows to be removed from Continue Watching.')
    parser.add_argument('--user', nargs='?',
                        help='User whose Continue Watching will be modified.')
    parser.add_argument('--playlists', nargs='+',
                        help='Shows in playlist to be removed from Continue Watching')
    parser.add_argument('--markWatched', action='store_true',
                        help='Mark episode as watched after removing from Continue Watching')
    
    opts = parser.parse_args()

    to_remove = []

    if opts.user:
        user_acct = account.user(opts.user)
        plex_server = PlexServer(PLEX_URL, user_acct.get_token(plex.machineIdentifier))
    else:
        plex_server = plex

    onDeck = [item for item in plex_server.library.onDeck() if item.type == 'episode']

    if opts.shows and not opts.playlists:
        for show in opts.shows:
            searched_show = plex_server.search(show, mediatype='show')[0]
            if searched_show.title == show:
                to_remove += searched_show.episodes()
    elif not opts.shows and opts.playlists:
        for pl in plex_server.playlists():
            if pl.title in opts.playlists:
                to_remove += pl.items()
    else:
        for item in onDeck:
            print('{}: S{:02}E{:02} {}'.format(item.grandparentTitle, int(item.parentIndex),
                                               int(item.index), item.title))

    for item in onDeck:
        if item in to_remove:
            print('Removing {}: S{:02}E{:02} {} from Continue Watching'.format(
                item.grandparentTitle, int(item.parentIndex), int(item.index), item.title))
            # item.removeFromContinueWatching()
            remove_from_cw(plex_server, item.ratingKey)
            if opts.markWatched:
                print('Marking as watched!')
                item.markPlayed()