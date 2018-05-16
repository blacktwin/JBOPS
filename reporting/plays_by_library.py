"""
Use Tautulli to pull plays by library
optional arguments:
  -h, --help            show this help message and exit
  -l  [ ...], --libraries  [ ...]
                        Space separated list of case sensitive names to process. Allowed names are:
                        (choices: All Library Names)


Usage:
   plays_by_library.py -l "TV Shows" Movies
      TV Shows - Plays: 2859
      Movies - Plays: 379
"""

import requests
import ConfigParser
import io
import os.path
import sys
import argparse
import json

TUTULLI_APIKEY = ''  # Your Tautulli API key
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

OUTPUT = '{section} - Plays: {plays}'

## CODE BELOW ##

def get_libraries_table(sections=None):
    # Get a list of new rating keys for the PMS of all of the item's parent/children.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_libraries_table',
               'order_column': 'plays'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        # print(json.dumps(response, indent=4, sort_keys=True))

        res_data = response['response']['data']['data']
        if sections:
            return [d for d in res_data if d['section_name'] in sections]
        else:
            return [d for d in res_data if d['section_name']]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_libraries_table' request failed: {0}.".format(e))


def main():

    lib_lst = [section['section_name'] for section in get_libraries_table()]

    parser = argparse.ArgumentParser(description="Use Tautulli to pull plays by library",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-l', '--libraries', nargs='+', type=str, choices=lib_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s)')

    opts = parser.parse_args()

    for section in get_libraries_table(opts.libraries):
        sec_name = section['section_name']
        sec_plays = section['plays']
        print(OUTPUT.format(section=sec_name, plays=sec_plays))


if __name__ == "__main__":
    main()
