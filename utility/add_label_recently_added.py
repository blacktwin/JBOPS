#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Description:  Automatically add a label to recently added items in your Plex library
Author:       /u/SwiftPanda16
Requires:     plexapi
Usage:
    python add_label_recently_added.py --rating_key 1234 --label "Label"

Tautulli script trigger:
    * Notify on recently added
Tautulli script conditions:
    * Filter which media to add labels to using conditions. Examples:
        [ Media Type | is | movie ]
        [ Show Name | is | Game of Thrones ]
        [ Album Name | is | Reputation ]
        [ Video Resolution | is | 4k ]
        [ Genre | contains | horror ]
Tautulli script arguments:
    * Recently Added:
        --rating_key {rating_key} --label "Label"
'''

import argparse
import os
from plexapi.server import PlexServer


# ## OVERRIDES - ONLY EDIT IF RUNNING SCRIPT WITHOUT TAUTULLI ##

PLEX_URL = ''
PLEX_TOKEN = ''

# Environmental Variables
PLEX_URL = PLEX_URL or os.getenv('PLEX_URL', PLEX_URL)
PLEX_TOKEN = PLEX_TOKEN or os.getenv('PLEX_TOKEN', PLEX_TOKEN)


def add_label_parent(plex, rating_key, label):
    item = plex.fetchItem(rating_key)

    if item.type in ('movie', 'show', 'album'):
        parent = item
    elif item.type in ('season', 'episode'):
        parent = item.show()
    elif item.type == 'track':
        parent = item.album()
    else:
        print(f"Cannot add label to '{item.title}' ({item.ratingKey}): Invalid media type '{item.type}'")
        return

    print(f"Adding label '{label}' to '{parent.title}' ({parent.ratingKey})")
    parent.addLabel(label)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rating_key', required=True, type=int)
    parser.add_argument('--label', required=True)
    opts = parser.parse_args()

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    add_label_parent(plex, **vars(opts))
