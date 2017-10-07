"""

Find what was added TFRAME ago and not watched using PlexPy.

"""

import requests
import sys
import time

TFRAME = 1.577e+7 # ~ 6 months in seconds
TODAY = time.time()


## EDIT THESE SETTINGS ##
PLEXPY_APIKEY = 'XXXXXX'  # Your PlexPy API key
PLEXPY_URL = 'http://localhost:8181/'  # Your PlexPy URL
LIBRARY_NAMES = ['My TV Shows', 'My Movies'] # Name of libraries you want to check.


class LIBINFO(object):
    def __init__(self, data=None):
        d = data or {}
        self.added_at = d['added_at']
        self.parent_rating_key = d['parent_rating_key']
        self.play_count = d['play_count']
        self.title = d['title']
        self.rating_key = d['rating_key']
        self.media_type = d['media_type']


class METAINFO(object):
    def __init__(self, data=None):
        d = data or {}
        self.added_at = d['added_at']
        self.parent_rating_key = d['parent_rating_key']
        self.title = d['title']
        self.rating_key = d['rating_key']
        self.media_type = d['media_type']
        self.grandparent_title = d['grandparent_title']
        self.file_size = d['file_size']
        self.file = d['file']


def get_get_new_rating_keys(rating_key, media_type):
    # Get a list of new rating keys for the PMS of all of the item's parent/children.
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_new_rating_keys',
               'rating_key': rating_key,
               'media_type': media_type}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']
        show = res_data['0']
        episode_lst = [episode['rating_key'] for _, season in show['children'].items() for _, episode in
                       season['children'].items()]

        return episode_lst

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_new_rating_keys' request failed: {0}.".format(e))


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
        # sys.stderr.write("PlexPy API 'get_get_metadata' request failed: {0}.".format(e))
        pass


def get_get_library_media_info(section_id):
    # Get the data on the PlexPy media info tables.
    payload = {'apikey': PLEXPY_APIKEY,
               'section_id': section_id,
               'cmd': 'get_library_media_info',
               'length': 10000}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return [LIBINFO(data=d) for d in res_data if d['play_count'] is None and (TODAY - int(d['added_at'])) > TFRAME]

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_library_media_info' request failed: {0}.".format(e))

def get_get_libraries_table():
    # Get the data on the PlexPy libraries table.
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_libraries_table'}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return [d['section_id'] for d in res_data if d['section_name'] in LIBRARY_NAMES]

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_libraries_table' request failed: {0}.".format(e))
        
def delete_files(tmp_lst):
    del_file = raw_input('Delete all unwatched files? (yes/no)').lower()
    if del_file.startswith('y'):
        for x in tmp_lst:
            print("Removing {}".format(x))
            os.remove(x)
    else:
        print('Ok. doing nothing.')

show_lst = []
path_lst = []

glt = [lib for lib in get_get_libraries_table()]

for i in glt:
    try:
        gglm = get_get_library_media_info(i)
        for x in gglm:
            try:
                if x.media_type in ['show', 'episode']:
                    # Need to find TV shows rating_key for episode.
                    show_lst += get_get_new_rating_keys(x.rating_key, x.media_type)
                else:
                    # Find movie rating_key.
                    show_lst += [int(x.rating_key)]
            except Exception as e:
                print("Rating_key failed: {e}").format(e=e)

    except Exception as e:
        print("Library media info failed: {e}").format(e=e)

# Remove reverse sort if you want the oldest keys first.
for i in sorted(show_lst, reverse=True):
    try:
        x = get_get_metadata(str(i))
        added = time.ctime(float(x.added_at))
        if x.grandparent_title == '' or x.media_type == 'movie':
            # Movies
            print(u"{x.title} ({x.rating_key}) was added {when} and has not been"
                  u"watched. \n File location: {x.file}".format(x=x, when=added))
        else:
            # Shows
            print(u"{x.grandparent_title}: {x.title} ({x.rating_key}) was added {when} and has"
                  u"not been watched. \n File location: {x.file}".format(x=x, when=added))
        path_lst += [x.file]

    except Exception as e:
        print("Metadata failed. Likely end of range: {e}").format(e=e)


delete_files(tmp_lst)
