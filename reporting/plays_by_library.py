"""
Use PlexPy to pull plays by library

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
import sys
import argparse
import json



# Load the configuration file
with open("../config.ini") as f:
    real_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=False)
config.readfp(io.BytesIO(real_config))

PLEXPY_APIKEY=config.get('plexpy-data', 'PLEXPY_APIKEY')
PLEXPY_URL=config.get('plexpy-data', 'PLEXPY_URL')

OUTPUT = '{section} - Plays: {plays}'

## CODE BELOW ##

def get_libraries_table(sections=None):
    # Get a list of new rating keys for the PMS of all of the item's parent/children.
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_libraries_table',
               'order_column': 'plays'}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        # print(json.dumps(response, indent=4, sort_keys=True))

        res_data = response['response']['data']['data']
        if sections:
            return [d for d in res_data if d['section_name'] in sections]
        else:
            return [d for d in res_data if d['section_name']]

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_libraries_table' request failed: {0}.".format(e))


def main():

    lib_lst = [section['section_name'] for section in get_libraries_table()]

    parser = argparse.ArgumentParser(description="Use PlexPy to pull plays by library",
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
