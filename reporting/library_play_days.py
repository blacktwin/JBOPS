"""
Use Tautulli to print plays by library from 0, 1, 7, or 30 days ago. 0 = total

optional arguments:
  -h, --help            show this help message and exit
  -l  [ ...], --libraries  [ ...]
                        Space separated list of case sensitive names to process. Allowed names are:
                        (choices: All Library Names)
  -d  [ ...], --days  [ ...]
                        Space separated list of case sensitive names to process. Allowed names are:
                        (defaults: [0, 1, 7, 30])
                         (choices: 0, 1, 7, 30)

Usage:
   plays_days.py -l "TV Shows" Movies -d 30 1 0
    Library: Movies
    Days: 1 : 30 : 0
    Plays: 5 : 83 : 384
    Library: TV Shows
    Days: 1 : 30 : 0
    Plays: 56 : 754 : 2899

"""

import requests
import sys
import argparse

## EDIT THESE SETTINGS ##

TAUTULLI_APIKEY = 'xxxxx'  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL

OUTPUT = 'Library: {section}\nDays: {days}\nPlays: {plays}'

## CODE BELOW ##

def get_library_names():
    # Get a list of new rating keys for the PMS of all of the item's parent/children.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_library_names'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        # print(json.dumps(response, indent=4, sort_keys=True))

        res_data = response['response']['data']
        return [d for d in res_data]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_library_names' request failed: {0}.".format(e))


def get_library_watch_time_stats(section_id):
    # Get a list of new rating keys for the PMS of all of the item's parent/children.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_library_watch_time_stats',
               'section_id': section_id}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        # print(json.dumps(response, indent=4, sort_keys=True))

        res_data = response['response']['data']
        return [d for d in res_data]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_library_watch_time_stats' request failed: {0}.".format(e))


def main():

    lib_lst = [section['section_name'] for section in get_library_names()]
    days_lst = [0, 1, 7, 30]

    parser = argparse.ArgumentParser(description="Use Tautulli to pull plays by library",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-l', '--libraries', nargs='+', type=str, default=lib_lst, choices=lib_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(defaults: %(default)s)\n (choices: %(choices)s)')
    parser.add_argument('-d', '--days', nargs='+', type=int, default=days_lst, choices=days_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(defaults: %(default)s)\n (choices: %(choices)s)')

    opts = parser.parse_args()

    for section in get_library_names():
        sec_name = section['section_name']
        if sec_name in opts.libraries:
            days = []
            plays = []
            section_id = section['section_id']
            for stats in get_library_watch_time_stats(section_id):
                if stats['query_days'] in opts.days and stats['total_plays'] > 0:
                    days.append(str(stats['query_days']))
                    plays.append(str(stats['total_plays']))

            print(OUTPUT.format(section=sec_name, days=' : '.join(days), plays=' : '.join(plays)))


if __name__ == "__main__":
    main()
