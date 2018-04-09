"""
usage: plex_netflix_check.py [-h] [-l  [...]] [-s ] [-t ]

Use instantwatcher.com to find if Plex items are on Netflix, Amazon, or both.

optional arguments:
  -h, --help            show this help message and exit
  -l  [ ...], --library  [ ...]
                        Space separated list of case sensitive names to process. Allowed names are:
                        (choices: Your show or movie library names)
  -s [], --search []    Search any name.
  -t [], --type []      Refine search for name by using type.
                        (choices: movie, show)
  -e [], --episodes []  Refine search for individual episodes.
                        (choices: True, False)
                        (default: False)
  -site [], --site []   Refine search for name by using type.
                        (choices: Netflix, Amazon, Both)
                        (default: Both)
  -sl [], --search_limit []
                        Define number of search returns from page. Zero returns all.
                        (default: 5)

If title is matched in both, Amazon is first then Netflix.
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
PLEX_TOKEN = 'xxxx'
## /Edit ##

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)


def instantwatch_search(name, media_type, site, search_limit):

    NETFLIX_URL = 'http://www.netflix.com/title/'
    limit = False
    results_count = 0

    if media_type == 'movie':
        content_type = '1'
    elif media_type == 'show':
        content_type = '2'
    elif media_type == 'episode':
        content_type = '4'
    else:
        content_type =''

    payload = {'content_type': content_type,
               'q': name.lower()}

    if site == 'Netflix':
        r = requests.get('http://instantwatcher.com/search'.rstrip('/'), params=payload)
    elif site == 'Amazon':
        r = requests.get('http://instantwatcher.com/a/search'.rstrip('/'), params=payload)
    else:
        r = requests.get('http://instantwatcher.com/u/search'.rstrip('/'), params=payload)

    results_lst = []
    res_data = bf.data(fromstring(r.content))

    res_data = res_data['html']['body']['div']['div'][1]

    # Any matches?
    res_results = res_data['div'][0]['div'][1]['div'][0]
    title_check = res_data['div'][0]['div'][1]['div'][1]

    try:
        if res_results['span']:
            total_results = res_results['span']
            for data in total_results:
                results_lst += [data['$']]
    except Exception:
        pass

    print('{} found {}.'.format(results_lst[0], results_lst[1]))
    result_count = int(results_lst[1].split(' ')[0])

    amazon_id = ''
    amazon_url = ''

    # Title match
    if result_count == 0:
        print('0 matches, moving on.')
        pass
    else:
        item_results_page = title_check['div']['div']
        if result_count > 1:
            for results in item_results_page:
                for data in results['a']:
                    try:
                        amazon_id = data['@data-amazon-title-id']
                        amazon_url = data['@data-amazon-uri']
                    except Exception:
                        pass

                for data in results['span']:
                    if data['@class'] == 'title' and search_limit is not 0:
                        if str(data['a']['$']).lower().startswith(name.lower()):
                            if amazon_id:
                                if data['a']['@data-title-id'] == amazon_id:
                                    print('Match found on Amazon for {}'.format(data['a']['$']))
                                    print('Page: {}'.format(amazon_url))
                                else:
                                    print('Match found on Netflix for {}'.format(data['a']['$']))
                                    print('Page: {}{}'.format(NETFLIX_URL, data['a']['@data-title-id']))
                            results_count += 1
                            search_limit -= 1
                            if search_limit is 0:
                                limit = True

                    elif data['@class'] == 'title' and search_limit is 0 and limit is False:
                        if data['a']['$'].lower().startswith(name.lower()):
                            if amazon_id:
                                if data['a']['@data-title-id'] == amazon_id:
                                    print('Match found on Amazon for {}'.format(data['a']['$']))
                                    print('Page: {}'.format(amazon_url))
                                else:
                                    print('Match found on Netflix for {}'.format(data['a']['$']))
                                    print('Page: {}{}'.format(NETFLIX_URL, data['a']['@data-title-id']))
                            results_count += 1

        elif result_count == 1:
            for data in item_results_page['a']:
                try:
                    amazon_id = data['@data-amazon-title-id']
                    amazon_url = data['@data-amazon-uri']
                except Exception:
                    pass
            for data in item_results_page['span']:
                if data['@class'] == 'title':
                    if data['a']['$'].lower().startswith(name.lower()):
                        print('Match! For {}'.format(data['a']['$']))
                        if amazon_id:
                            if data['a']['@data-title-id'] == amazon_id:
                                print('Page: {}'.format(amazon_url))
                        else:
                            print('Page: {}{}'.format(NETFLIX_URL, data['a']['@data-title-id']))
                        results_count += 1
                    else:
                        print('Could not find exact name match.')
    return results_count


def plex_library_search(lib_name, site, epi_search, search_limit):
    for title in plex.library.section(lib_name).all():
        print('Running check on {}'.format(title.title))
        file_path = []
        if title.type == 'show' and epi_search is True:
            if instantwatch_search(title.title, title.type, site, search_limit) > 0:
                print('Show was found. Searching for episode paths.')
                for episode in title.episodes():
                    # Need to check episodes against sites to truly find episode matches.
                    # For now just return paths for episodes if Show name matches.
                    # print('Running check on {} - {}'.format(title.title, episode.title))
                    # show_ep = '{} - {}'.format(title.title, episode.title)
                    # if instantwatch_search(show_ep, 'episode', site) > 0:
                    file_path += [episode.media[0].parts[0].file]

        elif title.type == 'movie':
            if instantwatch_search(title.title, title.type, site, search_limit) > 0:
                file_path = title.media[0].parts[0].file
        else:
            if instantwatch_search(title.title, title.type, site, search_limit) > 0:
                print('Show was found but path is not defined.')

        if file_path:
            if type(file_path) is str:
                print('File: {}'.format(file_path))
            elif type(file_path) is list:
                print('Files: \n{}'.format(' \n'.join(file_path)))

        print('Waiting 5 seconds before next search.')
        sleep(5)


def main():

    sections_lst = [d.title for d in plex.library.sections() if d.type in ['show', 'movie']]

    parser = argparse.ArgumentParser(description="Use instantwatcher.com to find if Plex items are on Netflix.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-l', '--library', metavar='', choices=sections_lst, nargs='+',
                        help='Space separated list of case sensitive names to process. Allowed names are:\n'
                             '(choices: %(choices)s)')
    parser.add_argument('-s', '--search', metavar='', nargs='?', type=str,
                        help='Search any name.')
    parser.add_argument('-m', '--media_type', metavar='', choices=['movie', 'show'], nargs='?',
                        help='Refine search for name by using media type.\n'
                             '(choices: %(choices)s)')
    parser.add_argument('-e', '--episodes', metavar='', nargs='?', type=bool, default=False, choices=[True, False],
                        help='Refine search for individual episodes.\n'
                             '(choices: %(choices)s)\n(default: %(default)s)')
    parser.add_argument('-site', '--site', metavar='', choices=['Netflix', 'Amazon', 'Both'], nargs='?',
                        default='Both', help='Refine search for name by using type.\n'
                             '(choices: %(choices)s)\n(default: %(default)s)')
    parser.add_argument('-sl', '--search_limit', metavar='', nargs='?', type=int, default=5,
                        help='Define number of search returns from page. Zero returns all.'
                             '\n(default: %(default)s)')

    opts = parser.parse_args()
    # print(opts)

    if opts.search:
        instantwatch_search(opts.search, opts.media_type, opts.site, opts.search_limit)
    else:
        if len(opts.library) > 1:
            for section in opts.library:
                plex_library_search(section, opts.site, opts.episodes, opts.search_limit)
        else:
            plex_library_search(opts.library[0], opts.site, opts.episodes, opts.search_limit)

if __name__ == '__main__':
    main()
