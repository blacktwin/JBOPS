#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Description:  Saves poster and art images from Plex to same folder as the media files.
Author:       /u/SwiftPanda16
Requires:     plexapi, tqdm (optional)
Usage:
    * Save posters for an entire library:
        python save_posters.py --library "TV Shows" --poster

    * Save art for an entire library:
        python save_posters.py --library "Music" --art

    * Save posters and art for an entire library:
        python save_posters.py --library "Movies" --poster --art

    * Save posters and art for a specific media type in a library:
        python save_posters.py --library "TV Shows" --libtype season --poster --art

    * Save posters for a specific item:
        python save_posters.py --rating_key 1234 --poster

    * Save art for a specific item:
        python save_posters.py --rating_key 1234 --art

    * Save posters and art for a specific item:
        python save_posters.py --rating_key 1234 --poster --art
'''

import argparse
from pathlib import Path
from plexapi.server import PlexServer
from plexapi.utils import download


PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'XXXXXXXXXXXXXXXXXXXX'
# Specify the mapped docker folder paths {host: container}. Leave blank {} if non-docker.
MAPPED_FOLDERS = {
    '/mnt/movies': '/movies',
    '/mnt/tvshows': '/tv',
}

_MAPPED_FOLDERS = {Path(host): Path(container) for host, container in MAPPED_FOLDERS.items()}


def map_path(file_path):
    for host, container in _MAPPED_FOLDERS.items():
        if container in file_path.parents:
            return host / file_path.relative_to(container)
    return file_path


def save_library(library, libtype=None, poster=False, art=False):
    for item in library.all(libtype=libtype, includeGuids=False):
        save_item(item, poster=poster, art=art)


def save_item(item, poster=False, art=False):
    if hasattr(item, 'locations'):
        file_path = Path(item.locations[0])
    else:
        file_path = Path(next(iter(item)).locations[0])
    save_path = map_path(file_path)
    if save_path.is_file():
        save_path = save_path.parent

    if poster:
        save_item_poster(item, save_path)
    if art:
        save_item_art(item, save_path)


def save_item_poster(item, save_path):
    print(f"Downloading poster for {item.title} to {save_path}")
    try:
        download(
            url=item.posterUrl,
            token=plex._token,
            filename='poster.jpg',
            savepath=save_path,
            showstatus=True  # Requires `tqdm` package
        )
    except Exception as e:
        print(f"Failed to download poster for {item.title}: {e}")


def save_item_art(item, save_path):
    print(f"Downloading art for {item.title} to {save_path}")
    try:
        download(
            url=item.artUrl,
            token=plex._token,
            filename='background.jpg',
            savepath=save_path,
            showstatus=True  # Requires `tqdm` package
        )
    except Exception as e:
        print(f"Failed to download art for {item.title}: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rating_key', type=int)
    parser.add_argument('--library')
    parser.add_argument('--libtype', choices=['movie', 'show', 'season', 'artist', 'album'])
    parser.add_argument('--poster', action='store_true')
    parser.add_argument('--art', action='store_true')
    opts = parser.parse_args()

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)

    if opts.rating_key:
        item = plex.fetchItem(opts.rating_key)
        save_item(item, opts.poster, opts.art)
    elif opts.library:
        library = plex.library.section(opts.library)
        save_library(library, opts.libtype, opts.poster, opts.art)
    else:
        print("No --rating_key or --library specified. Exiting.")
