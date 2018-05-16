'''
Run script by itself. Will look for WARN code followed by /library/metadata/ str in Plex logs.
This is find files that are corrupt or having playback issues.
I corrupted a file to test.
'''

import requests
import ConfigParser
import os.path
import io
import sys

TAUTULLI_APIKEY = ''  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8183/'  # Your Tautulli URL

## DO NOT EDIT
config_exists = os.path.exists("../config.ini")
if config_exists:
    # Load the configuration file
    with open("../config.ini") as f:
        real_config = f.read()
        config = ConfigParser.RawConfigParser(allow_no_value=False)
        config.readfp(io.BytesIO(real_config))

        TAUTULLI_APIKEY=config.get('tautulli-data', 'TAUTULLI_APIKEY')
        TAUTULLI_URL=config.get('tautulli-data', 'TAUTULLI_URL')
##/DO NOT EDIT

lib_met = []
err_title = []

class PlexLOG(object):
    def __init__(self, data=None):
        self.error_msg = []
        for e, f, g in data[0::1]:
            if f == 'WARN' and 'of key /library/metadata' in g:
                self.error_msg += [[f] + [g]]


class UserHIS(object):
    def __init__(self, data=None):
        data = data or {}
        self.title = [d['full_title'] for d in data]


def get_plex_log():
    # Get the user IP list from Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_plex_log'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']['data']

        return PlexLOG(data=res_data)

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_plex_log' request failed: {0}.".format(e))

def get_history(key):
    # Get the user IP list from Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'rating_key': key}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return UserHIS(data=res_data)

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))

if __name__ == '__main__':
    p_log = get_plex_log()
    for co, msg in p_log.error_msg:
        lib_met += [(msg.split('/library/metadata/'))[1].split(r'\n')[0]]
    for i in lib_met:
        his = get_history(int(i))
        err_title += [x.encode('UTF8') for x in his.title]
    err_title = ''.join((set(err_title)))
    print(err_title + ' is having playback issues')
