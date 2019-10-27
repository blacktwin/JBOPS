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
#        [ Media Type | is | episode ]
#    * Condition {2} (optional):
#        [ Library Name | is | DVR ]
#        [ Show Namme | is | Game of Thrones ]
# Tautulli script arguments:
#    * Recently Added:
#        To use an image file (can be image in the same directory as this script, or full path to an image):
#            --rating_key {rating_key} --file {file} --image spoilers.png
#        To blur the episode artwork (optional blur in pixels):
#            --rating_key {rating_key} --file {file} --blur 25
#    * Watched (optional):
#        --rating_key {rating_key} --file {file} --remove

import argparse
import os
import requests
import shutil
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
    parser.add_argument('--file', required=True)
    parser.add_argument('--image')
    parser.add_argument('--blur', type=int, default=25)
    parser.add_argument('--remove', action='store_true')
    opts = parser.parse_args()
    
    if opts.image:
        # File path to episode artwork using the same episode file name
        episode_artwork = os.path.splitext(opts.file)[0] + os.path.splitext(opts.image)[1]
        
        # Copy the image to the episode artwork
        shutil.copy2(opts.image, episode_artwork)
        
        # Refresh metadata for the TV show
        plex = PlexServer(PLEX_URL, PLEX_TOKEN)
        plex.fetchItem(opts.rating_key).show().refresh()
        
    elif opts.blur:
        # File path to episode artwork using the same episode file name
        episode_artwork = os.path.splitext(opts.file)[0] + '.png'
        
        # Get the blurred artwork from Tautulli
        blurred_artwork = get_blurred_image(opts.rating_key, opts.blur)
        if blurred_artwork:
            # Copy the image to the episode artwork
            with open(episode_artwork, 'wb') as f:
                shutil.copyfileobj(blurred_artwork, f)
            
            # Refresh metadata for the TV show
            plex = PlexServer(PLEX_URL, PLEX_TOKEN)
            plex.fetchItem(opts.rating_key).show().refresh()

    elif opts.remove:
        # File path to episode artwork using the same episode file name without extension
        episode_path = os.path.dirname(opts.file)
        episode_filename = os.path.splitext(os.path.basename(opts.file))[0]
        
        # Find image files with the same name as the episode
        for filename in os.listdir(episode_path):
            if filename.startswith(episode_filename) and filename.endswith(('.jpg', '.png')):
                # Delete the episode artwork image file
                os.remove(os.path.join(episode_path, filename))
        
        # Refresh metadata for the TV show
        plex = PlexServer(PLEX_URL, PLEX_TOKEN)
        plex.fetchItem(opts.rating_key).show().refresh()
