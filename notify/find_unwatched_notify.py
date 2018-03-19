"""

Find what was added TFRAME ago and not watched and notify admin using Tautulli.

TAUTULLI_URL + delete_media_info_cache?section_id={section_id}
"""

import requests
import sys
import time

TFRAME = 1.577e+7  # ~ 6 months in seconds
TODAY = time.time()

## EDIT THESE SETTINGS ##
TAUTULLI_APIKEY = ''  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8183/'  # Your Tautulli URL
LIBRARY_NAMES = ['Movies', 'TV Shows']  # Name of libraries you want to check.
SUBJECT_TEXT = "Tautulli Notification"
NOTIFIER_ID = 12  # The email notification agent ID for Tautulli


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
        media_info = d['media_info'][0]
        parts = media_info['parts'][0]
        self.file_size = parts['file_size']
        self.file = parts['file']


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


def get_metadata(rating_key):
    # Get the metadata for a media item.
    payload = {'apikey': TAUTULLI_APIKEY,
               'rating_key': rating_key,
               'cmd': 'get_metadata'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']
        return METAINFO(data=res_data)

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_metadata' request failed: {0}.".format(e))
        pass


def get_library_media_info(section_id):
    # Get the data on the Tautulli media info tables.
    payload = {'apikey': TAUTULLI_APIKEY,
               'section_id': section_id,
               'cmd': 'get_library_media_info'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']['data']
        return [LIBINFO(data=d) for d in res_data if d['play_count'] is None and (TODAY - int(d['added_at'])) > TFRAME]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_library_media_info' request failed: {0}.".format(e))


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


def send_notification(body_text):
    # Format notification text
    try:
        subject = SUBJECT_TEXT
        body = body_text
    except LookupError as e:
        sys.stderr.write("Unable to substitute '{0}' in the notification subject or body".format(e))
        return None
    # Send the notification through Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'notify',
               'notifier_id': NOTIFIER_ID,
               'subject': subject,
               'body': body}

    try:
        r = requests.post(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        if response['response']['result'] == 'success':
            sys.stdout.write("Successfully sent Tautulli notification.")
        else:
            raise Exception(response['response']['message'])
    except Exception as e:
        sys.stderr.write("Tautulli API 'notify' request failed: {0}.".format(e))
        return None


show_lst = []
notify_lst = []

libraries = [lib for lib in get_libraries_table()]

for library in libraries:
    try:
        library_media_info = get_library_media_info(library)
        for lib in library_media_info:
            try:
                if lib.media_type in ['show', 'episode']:
                    # Need to find TV shows rating_key for episode.
                    show_lst += get_new_rating_keys(lib.rating_key, lib.media_type)
                else:
                    # Find movie rating_key.
                    show_lst += [int(lib.rating_key)]
            except Exception as e:
                print "Rating_key failed: {e}".format(e=e)

    except Exception as e:
        print "Library media info failed: {e}".format(e=e)

for show in show_lst:
    try:
        meta = get_metadata(str(show))
        added = time.ctime(float(meta.added_at))
        if meta.grandparent_title == '' or meta.media_type == 'movie':
            # Movies
            notify_lst += [u"<dt>{x.title} ({x.rating_key}) was added {when} and has not been"
                           u" watched.</dt> <dd>File location: {x.file}</dd> <br>".format(x=meta, when=added)]
        else:
            # Shows
            notify_lst += [u"<dt>{x.grandparent_title}: {x.title} ({x.rating_key}) was added {when} and has"
                           u" not been watched.<d/t> <dd>File location: {x.file}</dd> <br>".format(x=meta, when=added)]

    except Exception as e:
        print "Metadata failed. Likely end of range: {e}".format(e=e)

if notify_lst:
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
    """.format(notify_lst="\n".join(notify_lst).encode("utf-8"), LIBRARY_NAMES=" & ".join(LIBRARY_NAMES))

    print(BODY_TEXT)
    send_notification(BODY_TEXT)
else:
    print('Nothing to report.')
    exit()
