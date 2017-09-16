"""
usage: stream_check_instantwatcher.py [-h] [-l  [...]] [-s ] [-t ]

Use instantwatcher.com to find if Plex items are on Netflix.

optional arguments:
  -h, --help            show this help message and exit
  -l  [ ...], --library  [ ...]
                        Space separated list of case sensitive names to process. Allowed names are:
                        (choices: Your show or movie library names)
  -s [], --search []    Search any name.
  -t [], --type []      Refine search for name by using type.

If site pulls more than 1 result, will check first 5 records.
search_limit = 5

"""

import requests
import argparse
from xmljson import badgerfish as bf
from lxml.html import fromstring
from time import sleep
import json
from plexapi.server import PlexServer
# pip install plexapi


## Edit ##
PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxxx'
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
## /Edit ##


def instantwatch_search(name, type):

    NETFLIX_URL = 'http://www.netflix.com/title/'
    search_limit = 5
    search = True

    if type == 'movie':
        content_type = '1'
    elif type == 'show':
        content_type = '3'
    else:
        content_type =''

    payload = {'content_type': content_type,
               'q': name.lower()}

    r = requests.get('http://instantwatcher.com/search'.rstrip('/'), params=payload)

    results_lst = []

    res_data = bf.data(fromstring(r.content))

    # with open('data.json', 'w') as outfile:
    #     json.dump(res_data, outfile, indent=4, sort_keys=True)

    res_data = res_data['html']['body']['div']['div'][1]

    # Any matches?
    results = res_data['div'][0]['div'][1]['div'][0]
    title_check = res_data['div'][0]['div'][1]['div'][1]

    try:
        if results['span']:
            total_results = results['span']
            for data in total_results:
                results_lst += [data['$']]
    except Exception:
        pass

    print('{} found {}.'.format(results_lst[0], results_lst[1]))
    result_count = int(results_lst[1].split(' ')[0])

    # Title match
    if result_count == 0:
        print('0 matches, moving on.')
        pass
    else:
        item_results_page = title_check['div']['div']
        if result_count > 1:
            for results in item_results_page:
                for data in results['span']:
                    if data['@class'] == 'title' and search is True and search_limit > 0:
                        if data['a']['$'].lower() == name.lower():
                            print('Match!')
                            print('Netflix Page: {}{}'.format(NETFLIX_URL, data['a']['@data-title-id']))
                            search = False
                        else:
                            print('Could not find exact name match.')
                            search_limit -= 1

        elif result_count == 1:
            for data in item_results_page['span']:
                if data['@class'] == 'title':
                    if data['a']['$'].lower() == name.lower():
                        print('Match!')
                        print('Netflix Page: {}{}'.format(NETFLIX_URL, data['a']['@data-title-id']))
                    else:
                        print('Could not find exact name match.')


def plex_library_search(lib_name):
    for t in plex.library.section(lib_name).all():
        print('Running check on {}'.format(t.title))
        instantwatch_search(t.title, t.type)
        print('Waiting 5 seconds before next search.')
        sleep(5)


def main():

    sections_lst = [d.title for d in plex.library.sections() if d.type in ['show', 'movie']]

    parser = argparse.ArgumentParser(description="Use instantwatcher.com to find if Plex items are on Netflix.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-l', '--library', metavar='', choices=sections_lst, nargs='+',
                        help='Space separated list of case sensitive names to process. Allowed names are:\n'
                             '(choices: %(choices)s)')
    parser.add_argument('-s', '--search', metavar='', nargs='?',
                        help='Search any name.')
    parser.add_argument('-t', '--type', metavar='', choices=['movie', 'show'], nargs='?',
                        help='Refine search for name by using type.')

    opts = parser.parse_args()
    # print(opts)

    if opts.search:
        instantwatch_search(opts.search, opts.type)
    else:
        if len(opts.library) > 1:
            for section in opts.library:
                plex_library_search(section)
        else:
            plex_library_search(opts.library[0])

if __name__ == '__main__':
    main()
