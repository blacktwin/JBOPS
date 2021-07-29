#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Description:  Automatically change episode artwork in Plex to hide spoilers.
# Author:       /u/SwiftPanda16
# Requires:     plexapi, requests
# Tautulli script trigger:
#    * Notify on recently added
#    * Notify on watched (optional - to remove the artwork after being watched)
# Tautulli script conditions:
#    * Condition {1}:
#        [Media Type | is | show or season or episode]
#    * Condition {2} (optional):
#        [ Library Name | is | DVR ]
#        [ Show Namme | is | Game of Thrones ]
# Tautulli script arguments:
#    * Recently Added:
#        To use an image file (can be image in the same directory as this script, or full path to an image):
#            --rating_key {rating_key} --image spoilers.png
#        To blur the episode artwork (optional blur in pixels):
#            --rating_key {rating_key} --blur 25
#        To add a prefix to the summary:
#            --rating_key --summary_prefix "** SPOILERS **"
#    * Watched (optional):
#        --rating_key {rating_key} --remove

from __future__ import unicode_literals
import argparse
import os
import requests
import shutil
import sys
from plexapi.server import PlexServer

TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''
PLEX_URL = ''
PLEX_TOKEN = ''

# Environmental Variables
TAUTULLI_URL = os.getenv('TAUTULLI_URL', TAUTULLI_URL)
TAUTULLI_APIKEY = os.getenv('TAUTULLI_APIKEY', TAUTULLI_APIKEY)
PLEX_URL = os.getenv('PLEX_URL', PLEX_URL)
PLEX_TOKEN = os.getenv('PLEX_TOKEN', PLEX_TOKEN)


def get_blurred_image(rating_key, blur=25):
    params = {'apikey': TAUTULLI_APIKEY,
              'cmd': 'pms_image_proxy',
              'img': '/library/metadata/{}/thumb'.format(rating_key),
              'width': 545,
              'height': 307,
              'opacity': 100,
              'background': '000000',
              'blur': blur,
              'img_format': 'png',
              'fallback': 'art'
              }

    r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=params, stream=True)
    if r.status_code == 200:
        r.raw.decode_content = True
        return r.raw


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--rating_key', required=True, type=int)
    parser.add_argument('--image')
    parser.add_argument('--blur', type=int, default=25)
    parser.add_argument('--summary_prefix')
    parser.add_argument('--remove', action='store_true')
    opts = parser.parse_args()

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    item = plex.fetchItem(opts.rating_key)

    if item.type == 'show':
        episodes = item.episodes()
        show = item
    elif item.type == 'season':
        episodes = item.episodes()
        show = item.show()
    elif item.type == 'episode':
        episodes = [item]
        show = item.show()
    else:
        print('Only media type show, season, or episode is supported: '
              '{item.title} ({item.ratingKey}) is media type {item.type}.'.format(item=item))
        sys.exit(0)

    for episode in episodes:
        for part in episode.iterParts():
            episode_filepath = part.file
            episode_folder = os.path.dirname(episode_filepath)
            episode_filename = os.path.splitext(os.path.basename(episode_filepath))[0]

            if opts.remove:
                # Find image files with the same name as the episode
                for filename in os.listdir(episode_folder):
                    if filename.startswith(episode_filename) and filename.endswith(('.jpg', '.png')):
                        # Delete the episode artwork image file
                        os.remove(os.path.join(episode_folder, filename))

                # Unlock the summary so it will get updated on refresh
                episode.edit(**{'summary.locked': 0})
                continue

            if opts.image:
                # File path to episode artwork using the same episode file name
                episode_artwork = os.path.splitext(episode_filepath)[0] + os.path.splitext(opts.image)[1]
                # Copy the image to the episode artwork
                shutil.copy2(opts.image, episode_artwork)

            elif opts.blur:
                # File path to episode artwork using the same episode file name
                episode_artwork = os.path.splitext(episode_filepath)[0] + '.png'
                # Get the blurred artwork from Tautulli
                blurred_artwork = get_blurred_image(episode.ratingKey, opts.blur)
                if blurred_artwork:
                    # Copy the image to the episode artwork
                    with open(episode_artwork, 'wb') as f:
                        shutil.copyfileobj(blurred_artwork, f)

            if opts.summary_prefix and not episode.summary.startswith(opts.summary_prefix):
                # Use a zero-width space (\u200b) for blank lines
                episode.edit(**{
                    'summary.value': opts.summary_prefix + '\n\u200b\n' + episode.summary,
                    'summary.locked': 1
                })

        # Refresh metadata for the episode
        episode.refresh()
