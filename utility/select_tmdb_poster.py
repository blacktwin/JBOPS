#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Description:  Selects the default TMDB poster if no poster is selected
              or the current poster is from Gracenote.
Author:       /u/SwiftPanda16
Requires:     plexapi
Usage:
    * Change the posters for an entire library:
        python select_tmdb_poster.py --library "Movies"

    * Change the poster for a specific item:
        python select_tmdb_poster.py --rating_key 1234

    * By default locked posters are skipped. To update locked posters:
        python select_tmdb_poster.py --library "Movies" --include_locked

Tautulli script trigger:
    * Notify on recently added
Tautulli script conditions:
    * Filter which media to select the poster. Examples:
        [ Media Type | is | movie ]
Tautulli script arguments:
    * Recently Added:
        --rating_key {rating_key}
'''

import argparse
import os
import plexapi.base
from plexapi.server import PlexServer
plexapi.base.USER_DONT_RELOAD_FOR_KEYS.add('fields')


# ## OVERRIDES - ONLY EDIT IF RUNNING SCRIPT WITHOUT TAUTULLI ##

PLEX_URL = ''
PLEX_TOKEN = ''

# Environmental Variables
PLEX_URL = PLEX_URL or os.getenv('PLEX_URL', PLEX_URL)
PLEX_TOKEN = PLEX_TOKEN or os.getenv('PLEX_TOKEN', PLEX_TOKEN)


def select_tmdb_poster_library(library, include_locked=False):
    for item in library.all(includeGuids=False):
        # Only reload for fields
        item.reload(**{k: 0 for k, v in item._INDLUCES.items()})
        select_tmdb_poster_item(item, include_locked=include_locked)


def select_tmdb_poster_item(item, include_locked=False):
    if item.isLocked('thumb') and not include_locked:
        print(f"Locked poster for {item.title}. Skipping.")
        return

    posters = item.posters()
    selected_poster = next((p for p in posters if p.selected), None)

    if selected_poster is None:
        print(f"WARNING: No poster selected for {item.title}.")
    else:
        skipping = ' Skipping.' if selected_poster.provider != 'gracenote' else ''
        print(f"Poster provider is '{selected_poster.provider}' for {item.title}.{skipping}")

    if selected_poster is None or selected_poster.provider == 'gracenote':
        # Fallback to first poster if no TMDB posters are available
        tmdb_poster = next((p for p in posters if p.provider == 'tmdb'), posters[0])
        # Selecting the poster automatically locks it
        tmdb_poster.select()
        print(f"Selected {tmdb_poster.provider} poster for {item.title}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rating_key', type=int)
    parser.add_argument('--library')
    parser.add_argument('--include_locked', action='store_true')
    opts = parser.parse_args()

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)

    if opts.rating_key:
        item = plex.fetchItem(opts.rating_key)
        select_tmdb_poster_item(item, opts.include_locked)
    elif opts.library:
        library = plex.library.section(opts.library)
        select_tmdb_poster_library(library, opts.include_locked)
    else:
        print("No --rating_key or --library specified. Exiting.")
