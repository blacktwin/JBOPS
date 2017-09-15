'''
Use instantwatcher.com to find if Plex items are on Netflix


'''
import requests
from xmljson import badgerfish as bf
from lxml.html import fromstring
from time import sleep
import json
from plexapi.server import PlexServer
# pip install plexapi


## Edit ##
PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxx'
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
## /Edit ##


def instantwatch_search(name, type):

    NETFLIX_URL = 'http://www.netflix.com/title/'

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

    # Title match
    if results_lst[1][0] == '0':
        print('0 matches, moving on.')
        pass
    else:
        item_results_page = title_check['div']['div']
        if results_lst[1][0] > '1':
            for results in item_results_page:
                for data in results['span']:
                    if data['@class'] == 'title':
                        if data['a']['$'].lower() == name.lower():
                            print('Match!')
                            print('Netflix Page: {}{}'.format(NETFLIX_URL, data['a']['@data-title-id']))
                        else:
                            print('Could not find exact name match.')

        elif results_lst[1][0] == '1':
            for data in item_results_page['span']:
                if data['@class'] == 'title':
                    if data['a']['$'].lower() == name.lower():
                        print('Match!')
                        print('Netflix Page: {}{}'.format(NETFLIX_URL, data['a']['@data-title-id']))
                    else:
                        print('Could not find exact name match.')


for t in plex.library.section('Movies').all():
    print('Running check on {}'.format(t.title))
    instantwatch_search(t.title, t.type)
    print('Waiting 5 seconds before next search.')
    sleep(5)

