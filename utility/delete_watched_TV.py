"""
From a list of TV shows, check if users in a list has watched shows episodes.
If all users in list have watched an episode of listed show, then delete episode.
"""

import requests
import ConfigParser
import io
import sys
import os

# Load the configuration file
with open("../config.ini") as f:
    real_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=False)
config.readfp(io.BytesIO(real_config))

PLEXPY_APIKEY=config.get('plexpy-data', 'PLEXPY_APIKEY')
PLEXPY_URL=config.get('plexpy-data', 'PLEXPY_URL')

# EDIT
SHOW_LST = [123456, 123456, 123456, 123456]  # Show rating keys.
USER_LST = ['Sam', 'Jakie', 'Blacktwin']  # Name of users


class UserHIS(object):
    def __init__(self, data=None):
        d = data or {}
        self.rating_key = d['rating_key']


class METAINFO(object):
    def __init__(self, data=None):
        d = data or {}
        self.title = d['title']
        self.file = d['file']
        self.media_type = d['media_type']
        self.grandparent_title = d['grandparent_title']


def get_get_metadata(rating_key):
    # Get the metadata for a media item.
    payload = {'apikey': PLEXPY_APIKEY,
               'rating_key': rating_key,
               'cmd': 'get_metadata',
               'media_info': True}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['metadata']
        return METAINFO(data=res_data)

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_get_metadata' request failed: {0}.".format(e))
        pass


def get_get_history(user, show, start, length):
    # Get the PlexPy history.
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_history',
               'user': user,
               'grandparent_rating_key': show,
               'start': start,
               'length': length}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return [UserHIS(data=d) for d in res_data if d['watched_status'] == 1]

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_history' request failed: {0}.".format(e))


meta_dict = {}
meta_lst = []
delete_lst = []

count = 25
for user in USER_LST:
    for show in SHOW_LST:
        start = 0
        while True:
            # Getting all watched history for listed users and shows
            history = get_get_history(user, show, start, count)
            try:
                if all([history]):
                    start += count
                    for h in history:
                        # Getting metadata of what was watched
                        meta = get_get_metadata(h.rating_key)
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
    for key, value in meta_dict.items():
        if value == USER_LST:
            print(u"{} {} has been watched by {}".format(meta_dict['grandparent_title'], meta_dict['title'],
                                                         " & ".join(USER_LST)))
            delete_lst.append(meta_dict['file'])

for x in delete_lst:
    print("Removing {}".format(x))
    os.remove(x)
