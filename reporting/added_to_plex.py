"""
Find when media was added between STARTFRAME and ENDFRAME to Plex through Tautulli.

Some Exceptions have been commented out to supress what is printed. 
Uncomment Exceptions if you run into problem and need to investigate.
"""

import requests
import sys
import time


STARTFRAME = 1480550400 # 2016, Dec 1 in seconds
ENDFRAME = 1488326400 # 2017, March 1 in seconds

TODAY = int(time.time())
LASTMONTH = int(TODAY - 2629743) # 2629743 = 1 month in seconds

# Uncomment to change range to 1 month ago - Today
# STARTFRAME = LASTMONTH
# ENDFRAME = TODAY


## EDIT THESE SETTINGS ##
TAUTULLI_APIKEY = 'XXXXX'  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL
LIBRARY_NAMES = ['TV Shows', 'Movies'] # Names of your libraries you want to check.


class LIBINFO(object):
    def __init__(self, data=None):
        d = data or {}
        self.added_at = d['added_at']
        self.parent_rating_key = d['parent_rating_key']
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


def get_new_rating_keys(rating_key, media_type):
    # Get a list of new rating keys for the PMS of all of the item's parent/children.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_new_rating_keys',
               'rating_key': rating_key,
               'media_type': media_type}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']
        show = res_data['0']
        episode_lst = [episode['rating_key'] for _, season in show['children'].items() for _, episode in
                       season['children'].items()]

        return episode_lst

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_new_rating_keys' request failed: {0}.".format(e))

def get_library_media_info(section_id):
    # Get the data on the Tautulli media info tables. Length matters!
    payload = {'apikey': TAUTULLI_APIKEY,
               'section_id': section_id,
               'order_dir ': 'asc',
               'cmd': 'get_library_media_info',
               'length': 10000000}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return [LIBINFO(data=d) for d in res_data]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_library_media_info' request failed: {0}.".format(e))

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
        if STARTFRAME <= int(res_data['added_at']) <= ENDFRAME:
            return METAINFO(data=res_data)

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_metadata' request failed: {0}.".format(e))

def update_library_media_info(section_id):
    # Get the data on the Tautulli media info tables.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_library_media_info',
               'section_id': section_id,
               'refresh': True}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.status_code
        if response != 200:
            print(r.content)

    except Exception as e:
        sys.stderr.write("Tautulli API 'update_library_media_info' request failed: {0}.".format(e))

def get_libraries_table():
    # Get the data on the Tautulli libraries table.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_libraries_table'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return [d['section_id'] for d in res_data if d['section_name'] in LIBRARY_NAMES]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_libraries_table' request failed: {0}.".format(e))


show_lst = []
count_lst = []
size_lst = []

glt = [lib for lib in get_libraries_table()]

# Updating media info for libraries.
[update_library_media_info(i) for i in glt]

for i in glt:
    try:
        gglm = get_library_media_info(i)
        for x in gglm:
            try:
                if x.media_type in ['show', 'episode']:
                    # Need to find TV shows rating_key for episode.
                    show_lst += get_new_rating_keys(x.rating_key, x.media_type)
                else:
                    # Find movie rating_key.
                    show_lst += [int(x.rating_key)]
            except Exception as e:
                print("Rating_key failed: {e}").format(e=e)

    except Exception as e:
        print("Library media info failed: {e}").format(e=e)

# All rating_keys for episodes and movies.
# Reserving order will put newest rating_keys first
# print(sorted(show_lst, reverse=True))

for i in sorted(show_lst, reverse=True):
    try:
        x = get_metadata(str(i))
        added = time.ctime(float(x.added_at))
        count_lst += [x.media_type]
        size_lst += [int(x.file_size)]
        if x.grandparent_title == '' or x.media_type == 'movie':
            # Movies
            print(u"{x.title} ({x.rating_key}) was added {when}.".format(x=x, when=added))
        else:
            # Shows
            print(u"{x.grandparent_title}: {x.title} ({x.rating_key}) was added {when}.".format(x=x, when=added))

    except Exception as e:
        # Remove commented print below to investigate problems.
        # print("Metadata failed. Likely end of range: {e}").format(e=e)
        # Remove break if not finding files in range
        break

print("There were {amount} files added between {start}:{end}".format(amount=len(count_lst),
                                                                     start=time.ctime(float(STARTFRAME)),
                                                                     end=time.ctime(float(ENDFRAME))))
print("Total movies: {}".format(count_lst.count('movie')))
print("Total shows: {}".format(count_lst.count('show') + count_lst.count('episode')))
print("Total size of files added: {}MB".format(sum(size_lst)>>20))
