#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Description:  Automatically lock/unlock posters and artwork in a Plex.
# Author:       /u/SwiftPanda16
# Requires:     plexapi
#
# Examples:
#     Lock poster for a specific rating key:
#         python lock_unlock_poster_art.py --rating_key 12345 --lock poster
#
#     Unlock artwork for a specific rating key:
#         python lock_unlock_poster_art.py --rating_key 12345 --unlock art
#
#     Lock all posters in "Movies" and "TV Shows" (Note: TV show libraries include season posters/artwork):
#         python lock_unlock_poster_art.py --libraries "Movies" "TV Shows" --lock poster
#
#     Lock all artwork in "Anime":
#         python lock_unlock_poster_art.py --libraries "Anime" --lock art
#
#     Lock all posters and artwork in "Movies" and "TV Shows":
#         python lock_unlock_poster_art.py --libraries "Movies" "TV Shows" --lock poster --lock art
#
#     Unlock all posters and artwork in "Music" (Note: Music libraries include album covers/artwork):
#         python lock_unlock_poster_art.py --libraries "Music" --unlock poster --unlock art

import argparse
import os
from plexapi.server import PlexServer

PLEX_URL = ''
PLEX_TOKEN = ''

# Environmental Variables
PLEX_URL = os.getenv('PLEX_URL', PLEX_URL)
PLEX_TOKEN = os.getenv('PLEX_TOKEN', PLEX_TOKEN)


def lock_unlock(plex, rating_key=None, libraries=None, lock=None, unlock=None):
    if rating_key:
        lock_unlock_items([plex.fetchItem(rating_key)], lock, unlock)

    if libraries is None:
        libraries = []

    for lib in libraries:
        library = plex.library.section(lib)
        lock_unlock_items(library.all(), lock, unlock)
        if library.TYPE == 'show':
            lock_unlock_items(library.all(libtype='season'), lock, unlock)
        elif library.TYPE == 'artist':
            lock_unlock_items(library.all(libtype='album'), lock, unlock)


def lock_unlock_items(items, lock, unlock):
    if lock is None:
        lock = []
    if unlock is None:
        unlock = []

    for item in items:
        if 'poster' in lock:
            item.lockPoster()
        if 'art' in lock:
            item.lockArt()
        if 'poster' in unlock:
            item.unlockPoster()
        if 'art' in unlock:
            item.unlockArt()


if __name__ == "__main__":
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    sections = [library.title for library in plex.library.sections()]
    lock_options = {'poster', 'art'}

    parser = argparse.ArgumentParser()
    parser.add_argument('--rating_key', type=int)
    parser.add_argument('--libraries', nargs='+', choices=sections)
    parser.add_argument('--lock', choices=lock_options, action='append')
    parser.add_argument('--unlock', choices=lock_options, action='append')
    opts = parser.parse_args()

    lock_unlock(plex, **vars(opts))
