#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
From a list of TV shows, check if users in a list has watched shows episodes.
If all users in list have watched an episode of listed show, then delete episode.

Add deletion via Plex.
"""
from __future__ import print_function
from __future__ import unicode_literals

from builtins import object
import requests
import sys
import os

# ## EDIT THESE SETTINGS ##
TAUTULLI_APIKEY = 'xxxxx'  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL
SHOW_LST = [123456, 123456, 123456, 123456]  # Show rating keys.
USER_LST = ['Sam', 'Jakie', 'Blacktwin']  # Name of users


class METAINFO(object):
    def __init__(self, data=None):
        d = data or {}
        self.title = d['title']
        media_info = d['media_info'][0]
        parts = media_info['parts'][0]
        self.file = parts['file']
        self.media_type = d['media_type']
        self.grandparent_title = d['grandparent_title']


def get_metadata(rating_key):
    # Get the metadata for a media item.
    payload = {'apikey': TAUTULLI_APIKEY,
               'rating_key': rating_key,
               'cmd': 'get_metadata',
               'media_info': True}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']
        return METAINFO(data=res_data)

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_metadata' request failed: {0}.".format(e))
        pass


def get_history(user, show, start, length):
    # Get the Tautulli history.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'user': user,
               'grandparent_rating_key': show,
               'start': start,
               'length': length}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return [d['rating_key'] for d in res_data if d['watched_status'] == 1]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))


meta_dict = {}
meta_lst = []
delete_lst = []

count = 25
for user in USER_LST:
    for show in SHOW_LST:
        start = 0
        while True:
            # Getting all watched history for listed users and shows
            history = get_history(user, show, start, count)
            try:
                if all([history]):
                    start += count
                    for rating_key in history:
                        # Getting metadata of what was watched
                        meta = get_metadata(rating_key)
                        if not any(d['title'] == meta.title for d in meta_lst):
                            meta_dict = {
                                'title': meta.title,
                                'file': meta.file,
                                'type': meta.media_type,
                                'grandparent_title': meta.grandparent_title,
                                'watched_by': [user]
                            }
                            meta_lst.append(meta_dict)
                        else:
                            for d in meta_lst:
                                if d['title'] == meta.title:
                                    d['watched_by'].append(user)
                    continue
                elif not all([history]):
                    break

                start += count
            except Exception as e:
                print(e)
                pass


for meta_dict in meta_lst:
    if set(USER_LST) == set(meta_dict['watched_by']):
        print("{} {} has been watched by {}".format(
            meta_dict['grandparent_title'].encode('UTF-8'),
            meta_dict['title'].encode('UTF-8'),
            " & ".join(USER_LST)))
        print("Removing {}".format(meta_dict['file']))
        os.remove(meta_dict['file'])
