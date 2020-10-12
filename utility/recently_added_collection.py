#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Description:  Automatically add a movie to a collection based on release date.
# Author:       /u/SwiftPanda16
# Requires:     plexapi
# Tautulli script trigger:
#    * Notify on recently added
# Tautulli script conditions:
#    * Filter which media to add to collection.
#        [ Media Type | is | movie ]
#        [ Library Name | is | Movies ]
# Tautulli script arguments:
#    * Recently Added:
#        --rating_key {rating_key} --collection "New Releases" --days 180

from __future__ import print_function
from __future__ import unicode_literals
import argparse
import os
from datetime import datetime, timedelta
from plexapi.server import PlexServer

PLEX_URL = ''
PLEX_TOKEN = ''

# Environmental Variables
PLEX_URL = os.getenv('PLEX_URL', PLEX_URL)
PLEX_TOKEN = os.getenv('PLEX_TOKEN', PLEX_TOKEN)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--rating_key', required=True, type=int)
    parser.add_argument('--collection', required=True)
    parser.add_argument('--days', required=True, type=int)
    opts = parser.parse_args()

    threshold_date = datetime.now() - timedelta(days=opts.days)
    
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    
    movie = plex.fetchItem(opts.rating_key)
    
    if movie.originallyAvailableAt >= threshold_date:
        movie.addCollection(opts.collection)
        print("Added collection '{}' to '{}'.".format(opts.collection, movie.title.encode('UTF-8')))
        
    for m in movie.section().search(collection=opts.collection):
        if m.originallyAvailableAt < threshold_date:
            m.removeCollection(opts.collection)
            print("Removed collection '{}' from '{}'.".format(opts.collection, m.title.encode('UTF-8')))
