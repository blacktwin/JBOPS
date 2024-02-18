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

    * Ignore locked posters:
        python select_tmdb_poster.py --library "Movies" --ignore_locked

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


def select_tmdb_poster_library(library, ignore_locked=False):
    for item in library.all(includeGuids=False):
        # Only reload for fields
        item.reload(
            checkFiles=0,
            includeAllConcerts=0,
            includeBandwidths=0,
            includeChapters=0,
            includeChildren=0,
            includeConcerts=0,
            includeExternalMedia=0,
            includeExtras=0,
            includeFields=1,
            includeGeolocation=0,
            includeLoudnessRamps=0,
            includeMarkers=0,
            includeOnDeck=0,
            includePopularLeaves=0,
            includePreferences=0,
            includeRelated=0,
            includeRelatedCount=0,
            includeReviews=0,
            includeStations=0
        )
        select_tmdb_poster_item(item, ignore_locked=ignore_locked)


def select_tmdb_poster_item(item, ignore_locked=False):
    posters = item.posters()
    selected_poster = next((p for p in posters if p.selected), None)

    if selected_poster is None or not item.isLocked('thumb'):
        print(f"WARNING: No poster selected for {item.title}")
        select_tmdb_poster(item, posters)
    elif not ignore_locked and item.isLocked('thumb'):
        print(f"Poster is locked for {item.title}. Skipping.")
    elif selected_poster.provider == 'gracenote':
        select_tmdb_poster(item, posters)


def select_tmdb_poster(item, posters):
    # Fallback to first poster if no TMDB posters are available
    tmdb_poster = next((p for p in posters if p.provider == 'tmdb'), posters[0])
    # Selecting the poster automatically locks it
    tmdb_poster.select()
    print(f"Selected {tmdb_poster.provider} poster for {item.title}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rating_key', type=int)
    parser.add_argument('--library')
    parser.add_argument('--ignore_locked', action='store_true')
    opts = parser.parse_args()

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)

    if opts.rating_key:
        item = plex.fetchItem(opts.rating_key)
        select_tmdb_poster_item(item, opts.ignore_locked)
    elif opts.library:
        library = plex.library.section(opts.library)
        select_tmdb_poster_library(library, opts.ignore_locked)
    else:
        print("No --rating_key or --library specified. Exiting.")
