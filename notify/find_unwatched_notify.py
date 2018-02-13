"""

Find what was added TFRAME ago and not watched and notify admin using PlexPy.

"""

import requests
import ConfigParser
import io
import sys
import time

TFRAME = 1.577e+7 # ~ 6 months in seconds
TODAY = time.time()


# Load the configuration file
with open("../config.ini") as f:
    real_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=False)
config.readfp(io.BytesIO(real_config))

PLEXPY_APIKEY=config.get('plexpy-data', 'PLEXPY_APIKEY')
PLEXPY_URL=config.get('plexpy-data', 'PLEXPY_URL')

## EDIT THESE SETTINGS ##
LIBRARY_NAMES = ['My Movies', 'My TV Shows'] # Name of libraries you want to check.
SUBJECT_TEXT = "PlexPy Notification"
AGENT_ID = 10  # The email notification agent ID for PlexPy


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

def send_notification(BODY_TEXT):
    # Format notification text
    try:
        subject = SUBJECT_TEXT
        body = BODY_TEXT
    except LookupError as e:
        sys.stderr.write("Unable to substitute '{0}' in the notification subject or body".format(e))
        return None
    # Send the notification through PlexPy
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'notify',
               'agent_id': AGENT_ID,
               'subject': subject,
               'body': body}

    try:
        r = requests.post(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        if response['response']['result'] == 'success':
            sys.stdout.write("Successfully sent PlexPy notification.")
        else:
            raise Exception(response['response']['message'])
    except Exception as e:
        sys.stderr.write("PlexPy API 'notify' request failed: {0}.".format(e))
        return None


show_lst = []
notify_lst = []

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

for i in show_lst:
    try:
        x = get_get_metadata(str(i))
        added = time.ctime(float(x.added_at))
        if x.grandparent_title == '' or x.media_type == 'movie':
            # Movies
            notify_lst += [u"<dt>{x.title} ({x.rating_key}) was added {when} and has not been"
                  u" watched.</dt> <dd>File location: {x.file}</dd> <br>".format(x=x, when=added)]
        else:
            # Shows
            notify_lst += [u"<dt>{x.grandparent_title}: {x.title} ({x.rating_key}) was added {when} and has"
                  u" not been watched.<d/t> <dd>File location: {x.file}</dd> <br>".format(x=x, when=added)]

    except Exception as e:
        print("Metadata failed. Likely end of range: {e}").format(e=e)


BODY_TEXT = """\
<html>
  <head></head>
  <body>
    <p>Hi!<br>
    <br>Below is the list of {LIBRARY_NAMES} that have not been watched.<br>
    <dl>
    {notify_lst}
    </dl>
    </p>
  </body>
</html>
""".format(notify_lst="\n".join(notify_lst).encode("utf-8"),LIBRARY_NAMES=" & ".join(LIBRARY_NAMES))

send_notification(BODY_TEXT)
