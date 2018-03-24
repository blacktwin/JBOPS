"""
Find Movies that have been watched by a list of users. 
If all users have watched movie than delete.

Deletion is prompted
"""

import requests
import sys
import os
import shutil


## EDIT THESE SETTINGS ##
TAUTULLI_APIKEY = 'xxxxxxxx'  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL
LIBRARY_NAMES = ['My Movies'] # Whatever your movie libraries are called.
USER_LST = ['Joe', 'Alex'] # Name of users

class UserHIS(object):
    def __init__(self, data=None):
        d = data or {}
        self.rating_key = d['rating_key']


class METAINFO(object):
    def __init__(self, data=None):
        d = data or {}
        self.title = d['title']
        media_info = d['media_info'][0]
        parts = media_info['parts'][0]
        self.file = parts['file']


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
        if res_data['library_name'] in LIBRARY_NAMES:
            return METAINFO(data=res_data)

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_metadata' request failed: {0}.".format(e))
        pass


def get_history(user, start, length):
    # Get the Tautulli history.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'user': user,
               'media_type': 'movie',
               'start': start,
               'length': length}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return [UserHIS(data=d) for d in res_data if d['watched_status'] == 1]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))


def delete_files(tmp_lst):
    del_file = raw_input('Delete all watched files? (yes/no)').lower()
    if del_file.startswith('y'):
        for x in tmp_lst:
            print("Removing {}".format(os.path.dirname(x)))
            shutil.rmtree(os.path.dirname(x))
    else:
        print('Ok. doing nothing.')

movie_dict = {}
movie_lst = []
delete_lst = []

count = 25
for user in USER_LST:
    start = 0
    while True:
        # Getting all watched history for listed users
        history = get_history(user, start, count)
        try:
            if all([history]):
                start += count
                for h in history:
                    # Getting metadata of what was watched
                    movies = get_metadata(h.rating_key)
                    if not any(d['title'] == movies.title for d in movie_lst):
                        movie_dict = {
                            'title': movies.title,
                            'file': movies.file,
                            'watched_by': [user]
                        }
                        movie_lst.append(movie_dict)
                    else:
                        for d in movie_lst:
                            if d['title'] == movies.title:
                                d['watched_by'].append(user)
                continue
            elif not all([history]):
                break

            start += count
        except Exception as e:
            print(e)
            pass

for movie_dict in movie_lst:
    for key, value in movie_dict.items():
        if value == USER_LST:
            print(u"{} has been watched by {}".format(movie_dict['title']," & ".join(USER_LST)))
            delete_lst.append(movie_dict['file'])

delete_files(delete_lst)
