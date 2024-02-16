#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Description: Automatically add a label to recently added items in 
                your Plex library, based on a list of tags and if the 
                media's filepath contains one of those tags an assigns the label dynamically.
Author:    DaTurkeyslayer + SwiftPanda16 + Blacktwin
Requires:   plexapi
Usage:
  python add_label_recently_added.py --rating_key 1234 --tags 'John,Jane,Alice,4K'

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
    --rating_key {rating_key} --tagsList John,Jane,Alice
'''

import argparse
import os
import plexapi
from plexapi.server import PlexServer

# ## OVERRIDES - ONLY EDIT IF RUNNING SCRIPT WITHOUT TAUTULLI ##

PLEX_URL = ''
PLEX_TOKEN = ''

# Environmental Variables
PLEX_URL = PLEX_URL or os.getenv('PLEX_URL', PLEX_URL)
PLEX_TOKEN = PLEX_TOKEN or os.getenv('PLEX_TOKEN', PLEX_TOKEN)

def add_label_parent(plex, rating_key, tags):
    item = plex.fetchItem(rating_key)

    if item.type in ('movie', 'show', 'album'):
        mediaRecord = item
    elif item.type in ('episode'):
        mediaRecord = item.show()
    elif item.type == 'track':
        mediaRecord = item.album()
    else:
        print(f"Cannot add label to '{item.title}' ({item.ratingKey}): Invalid media type '{item.type}'")
        return

    # Get all of the items filepaths and save them to a list
    filepaths = item.locations
    
    # Loop through each filepath for the item 
    for filepath in filepaths:
        # Loop through each tag to check if it is in the current filepath
        for tag in tags:
            # Check if the tag is in the filepath
            if tag.lower() in filepath.lower():
                # Use the found tag to dynamically assign the label
                dynamic_label = tag + "'s"
                
                # Check if the label already exists
                existing_labels = [label.tag for label in mediaRecord.labels]
                
                if dynamic_label not in existing_labels:
                    # Create the label if it doesn't exist
                    mediaRecord.addLabel(dynamic_label)
                    print(f"Adding label '{dynamic_label}' to '{mediaRecord.title}' ({mediaRecord.ratingKey})")
    else:
        print(f"No matching tag found in any of the file paths for '{mediaRecord.title}' ({mediaRecord.ratingKey})")
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rating_key', required=True, type=int)
    parser.add_argument('--tagsList', type=str, required=True, help='Comma-separated list of tags')
    opts = parser.parse_args()

    # Parse comma-separated tags
    tags = [tag.strip() for tag in opts.tagsList.split(',')] if opts.tagsList else []

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    add_label_parent(plex, opts.rating_key, tags)
