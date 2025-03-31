#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Description:  Selects the default TMDB poster and art for items in a Plex library
              if no poster/art is selected or the current poster/art is from Gracenote.
Author:       /u/SwiftPanda16
Requires:     plexapi
Usage:
    * Change the posters for an entire library:
        python select_tmdb_poster.py --library "Movies" --poster

    * Change the art for an entire library:
        python select_tmdb_poster.py --library "Movies" --art

    * Change the posters and art for an entire library:
        python select_tmdb_poster.py --library "Movies" --poster --art

    * Change the poster for a specific item:
        python select_tmdb_poster.py --rating_key 1234 --poster

    * Change the art for a specific item:
        python select_tmdb_poster.py --rating_key 1234 --art

    * Change the poster and art for a specific item:
        python select_tmdb_poster.py --rating_key 1234 --poster --art

    * By default locked posters are skipped. To update locked posters:
        python select_tmdb_poster.py --library "Movies" --include_locked --poster --art

    * To override the preferred provider:
        python select_tmdb_poster.py --library "Movies" --art --art_provider "fanarttv"

Tautulli script trigger:
    * Notify on recently added
Tautulli script conditions:
    * Filter which media to select the poster. Examples:
        [ Media Type | is | movie ]
Tautulli script arguments:
    * Recently Added:
        --rating_key {rating_key} --poster --art
'''

import argparse
import os
import plexapi.base
from plexapi.server import PlexServer
plexapi.base.USER_DONT_RELOAD_FOR_KEYS.add('fields')


# Poster and art providers to replace
REPLACE_PROVIDERS = ['gracenote', 'plex', None]

# Preferred poster and art provider to use (Note not all providers are availble for all items)
# Possible options: tmdb, tvdb, imdb, fanarttv, gracenote, plex
PREFERRED_POSTER_PROVIDER = 'tmdb'
PREFERRED_ART_PROVIDER = 'tmdb'


# ## OVERRIDES - ONLY EDIT IF RUNNING SCRIPT WITHOUT TAUTULLI ##

PLEX_URL = ''
PLEX_TOKEN = ''

# Environmental Variables
PLEX_URL = PLEX_URL or os.getenv('PLEX_URL', PLEX_URL)
PLEX_TOKEN = PLEX_TOKEN or os.getenv('PLEX_TOKEN', PLEX_TOKEN)


def select_library(
    library,
    include_locked=False,
    poster=False,
    poster_provider=PREFERRED_POSTER_PROVIDER,
    art=False,
    art_provider=PREFERRED_ART_PROVIDER
):
    for item in library.all(includeGuids=False):
        # Only reload for fields
        item.reload(**{k: 0 for k, v in item._INCLUDES.items()})
        select_item(
            item,
            include_locked=include_locked,
            poster=poster,
            poster_provider=poster_provider,
            art=art,
            art_provider=art_provider
        )


def select_item(
    item,
    include_locked=False,
    poster=False,
    poster_provider=PREFERRED_POSTER_PROVIDER,
    art=False,
    art_provider=PREFERRED_ART_PROVIDER
):
    print(f"{item.title} ({item.year})")

    if poster:
        select_poster(item, include_locked, poster_provider)
    if art:
        select_art(item, include_locked, art_provider)


def select_poster(item, include_locked=False, provider=PREFERRED_POSTER_PROVIDER):
    print("  Checking poster...")

    if item.isLocked('thumb') and not include_locked:  # PlexAPI 4.5.10
        print(f"  - Locked poster for {item.title}. Skipping.")
        return

    posters = item.posters()
    selected_poster = next((p for p in posters if p.selected), None)

    if selected_poster is None:
        print(f"  - WARNING: No poster selected for {item.title}.")
    else:
        skipping_poster = ' Skipping.' if selected_poster.provider not in REPLACE_PROVIDERS else ''
        print(f"  - Poster provider is '{selected_poster.provider}' for {item.title}.{skipping_poster}")

    if posters and (selected_poster is None or selected_poster.provider in REPLACE_PROVIDERS):
        # Fallback to first poster if no preferred provider posters are available
        provider_poster = next((p for p in posters if p.provider == provider), posters[0])
        # Selecting the poster automatically locks it
        provider_poster.select()
        print(f"  - Selected {provider_poster.provider} poster for {item.title}.")


def select_art(item, include_locked=False, provider=PREFERRED_ART_PROVIDER):
    print("  Checking art...")

    if item.isLocked('art') and not include_locked:  # PlexAPI 4.5.10
        print(f"  - Locked art for {item.title}. Skipping.")
        return

    arts = item.arts()
    selected_art = next((p for p in arts if p.selected), None)

    if selected_art is None:
        print(f"  - WARNING: No art selected for {item.title}.")
    else:
        skipping_art = ' Skipping.' if selected_art.provider not in REPLACE_PROVIDERS else ''
        print(f"  - Art provider is '{selected_art.provider}' for {item.title}.{skipping_art}")

    if arts and (selected_art is None or selected_art.provider in REPLACE_PROVIDERS):
        # Fallback to first art if no preferred provider arts are available
        provider_art = next((p for p in arts if p.provider == provider), arts[0])
        # Selecting the art automatically locks it
        provider_art.select()
        print(f"  - Selected {provider_art.provider} art for {item.title}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rating_key', type=int)
    parser.add_argument('--library')
    parser.add_argument('--include_locked', action='store_true')
    parser.add_argument('--poster', action='store_true')
    parser.add_argument('--poster_provider', default=PREFERRED_POSTER_PROVIDER)
    parser.add_argument('--art', action='store_true')
    parser.add_argument('--art_provider', default=PREFERRED_ART_PROVIDER)
    opts = parser.parse_args()

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)

    if opts.rating_key:
        item = plex.fetchItem(opts.rating_key)
        select_item(item, opts.include_locked, opts.poster, opts.poster_provider, opts.art, opts.art_provider)
    elif opts.library:
        library = plex.library.section(opts.library)
        select_library(library, opts.include_locked, opts.poster, opts.poster_provider, opts.art, opts.art_provider)
    else:
        print("No --rating_key or --library specified. Exiting.")
