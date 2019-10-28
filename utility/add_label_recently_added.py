#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Description:  Automatically add a label to recently added items in your Plex library
# Author:       /u/SwiftPanda16
# Requires:     requests
# Tautulli script trigger:
#    * Notify on recently added
# Tautulli script conditions:
#    * Filter which media to add labels to using conditions. Examples:
#        [ Media Type | is | movie ]
#        [ Show Name | is | Game of Thrones ]
#        [ Album Name | is | Reputation ]
#        [ Video Resolution | is | 4k ]
#        [ Genre | contains | horror ]
# Tautulli script arguments:
#    * Recently Added:
#        --title {title} --section_id {section_id} --media_type {media_type} --rating_key {rating_key}  --parent_rating_key {parent_rating_key} --grandparent_rating_key {grandparent_rating_key} --label "Label"

import argparse
import os
import requests


### OVERRIDES - ONLY EDIT IF RUNNING SCRIPT WITHOUT TAUTULLI ###

PLEX_URL = ''
PLEX_TOKEN = ''


### CODE BELOW ###

PLEX_URL = PLEX_URL or os.getenv('PLEX_URL', PLEX_URL)
PLEX_TOKEN = PLEX_TOKEN or os.getenv('PLEX_TOKEN', PLEX_TOKEN)

MEDIA_TYPES_PARENT_VALUES = {'movie': 1, 'show': 2, 'season': 2, 'episode': 2, 'album': 9, 'track': 9}


def add_label(media_type_value, rating_key, section_id, label):
    headers = {'X-Plex-Token': PLEX_TOKEN}
    params = {'type': media_type_value,
              'id': rating_key,
              'label.locked': 1,
              'label[0].tag.tag': label
              }

    url = '{base_url}/library/sections/{section_id}/all'.format(base_url=PLEX_URL, section_id=section_id)
    r = requests.put(url, headers=headers, params=params)

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--title', required=True)
    parser.add_argument('--section_id', required=True)
    parser.add_argument('--media_type', required=True)
    parser.add_argument('--rating_key', required=True)
    parser.add_argument('--parent_rating_key', required=True)
    parser.add_argument('--grandparent_rating_key', required=True)
    parser.add_argument('--label', required=True)
    opts = parser.parse_args()
    
    if opts.media_type not in MEDIA_TYPES_PARENT_VALUES:
        print("Cannot add label to '{opts.title}': Invalid media type '{opts.media_type}'".format(opts=opts))
    else:
        media_type_value = MEDIA_TYPES_PARENT_VALUES[opts.media_type]
        rating_key = ''
        
        if opts.media_type in ('movie', 'show', 'album'):
            rating_key = opts.rating_key
        elif opts.media_type in ('season', 'track'):
            rating_key = opts.parent_rating_key
        elif opts.media_type in ('episode'):
            rating_key = opts.grandparent_rating_key
            
        if rating_key and rating_key.isdigit():
            add_label(media_type_value, int(rating_key), opts.section_id, opts.label)
            print("The label '{opts.label}' was added to '{opts.title}' ({rating_key}).".format(opts=opts, rating_key=rating_key))
        else:
            print("Cannot add label to '{opts.title}': Invalid rating key '{rating_key}'".format(opts=opts, rating_key=rating_key))
