#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Description:  Automatically mark a multi-episode file as watched in Plex.
# Author:       /u/SwiftPanda16
# Requires:     plexapi
# Tautulli script trigger:
#    * Notify on watched
# Tautulli script conditions:
#    * Condition {1}:
#        [ Media Type | is | episode ]
#    * Condition {2} (optional):
#        [ Username | is | username ]
# Tautulli script arguments:
#    * Watched:
#        --rating_key {rating_key} --filename {filename}

from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import argparse
import os
from plexapi.server import PlexServer

PLEX_URL = ''
PLEX_TOKEN = ''

# Environmental Variables
PLEX_URL = os.getenv('PLEX_URL', PLEX_URL)
PLEX_USER_TOKEN = os.getenv('PLEX_USER_TOKEN', PLEX_TOKEN)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--rating_key', required=True, type=int)
    parser.add_argument('--filename', required=True)
    opts = parser.parse_args()

    plex = PlexServer(PLEX_URL, PLEX_USER_TOKEN)
    
    for episode in plex.fetchItem(opts.rating_key).season().episodes():
        if episode.ratingKey == opts.rating_key:
            continue
        if any(opts.filename in part.file for media in episode.media for part in media.parts):
            print("Marking multi-episode file '{grandparentTitle} - S{parentIndex}E{index}' as watched.".format(
                grandparentTitle=episode.grandparentTitle.encode('UTF-8'),
                parentIndex=str(episode.parentIndex).zfill(2),
                index=str(episode.index).zfill(2)))
            episode.markWatched()
