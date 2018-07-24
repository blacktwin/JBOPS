"""
Description: Comparing content between two or more Plex servers.
              Creates .json file in script directory of server compared.
              .json file contents include list items by media types (movie, show)
              type combined between server 1 and server 2
              type missing (_mine) from s2 but found in s1
              type missing (_missing) from s1 but found in s2
              type shared (_shared) between s1 and s2
Author: Blacktwin
Requires: requests, plexapi

 Example:
    python find_diff_other_servers.py --server "My Plex Server" --server PlexServer2
    python find_diff_other_servers.py --server "My Plex Server" --server PlexServer2 --server "Steven Plex"

"""

import argparse
import requests
import json
import sys
from plexapi.server import PlexServer, CONFIG

TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''
TAUTULLI_URL = CONFIG.data['auth'].get('tautulli_baseurl', TAUTULLI_URL)
TAUTULLI_APIKEY = CONFIG.data['auth'].get('tautulli_apikey', TAUTULLI_APIKEY)

PLEX_URL = ''
PLEX_TOKEN = ''
PLEX_URL = CONFIG.data['auth'].get('server_baseurl', PLEX_URL)
PLEX_TOKEN = CONFIG.data['auth'].get('server_token', PLEX_TOKEN)

# Sections to ignore from comparision.
IGNORE_LST = ['Library name']

sess = requests.Session()
# Ignore verifying the SSL certificate
sess.verify = False  # '/path/to/certfile'
# If verify is set to a path to a directory,
# the directory must have been processed using the c_rehash utility supplied
# with OpenSSL.
if sess.verify is False:
    # Disable the warning that the request is insecure, we know that...
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

SERVER_DICT = {server.name: server for server in
               plex.myPlexAccount().resources()
               if 'server' in server.provides.split(',')}

shared_lst = []


def find_things(server):
    dict_tt = {'movie': [], 'show': []}
    print('Finding items from {}.'.format(server.friendlyName))
    for section in server.library.sections():
        if section.title not in IGNORE_LST and section.type in ['movie', 'show']:
            for item in server.library.section(section.title).all():
                dict_tt[section.type].append(server.fetchItem(item.ratingKey))

    return dict_tt


def org_diff(main_key, friend_key, diff):

    if diff == 'mine':
        return list(set(main_key) - set(friend_key))
    elif diff == 'missing':
        return list(set(friend_key) - set(main_key))
    elif diff == 'combined':
        return list(set(friend_key + main_key))


def diff_things(main_dict, friend_dict):

    for key in main_dict.keys():
        main_titles = [x.title for x in main_dict[key]]
        friend_titles = [x.title for x in friend_dict[key]]

        mine = org_diff(main_titles, friend_titles, 'mine')
        missing = org_diff(main_titles, friend_titles, 'missing')
        shared = set(main_titles + friend_titles)
        print('... combining {}s'.format(key))
        main_dict['{}_combined'.format(key)] = org_diff(main_titles, friend_titles, 'combined')

        print('... comparing {}s'.format(key))
        print('... finding what is mine')
        main_dict['{}_mine'.format(key)] = mine
        print('... finding what is missing')
        main_dict['{}_missing'.format(key)] = missing
        print('... finding what is shared')
        ddiff = set(mine + missing)
        shared_lst = list(shared.union(ddiff) - shared.intersection(ddiff))
        main_dict['{}_shared'.format(key)] = shared_lst

    return main_dict


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Comparing content between two or more Plex servers.")
    parser.add_argument('--server', required=True, choices=SERVER_DICT.keys(),
                        action='append', nargs='?', metavar='',
                        help='Choose servers to connect to and compare.'
                             '\nChoices: (%(choices)s)')

    opts = parser.parse_args()

    if len(opts.server) < 2:
        sys.stderr.write("Need more than one server to compare.\n")
        sys.exit(1)

    server_compare = SERVER_DICT[opts.server[0]]
    main_server = server_compare.connect()
    print('Connected to {} server.'.format(main_server.friendlyName))

    for server in opts.server[1:]:
        other_server = SERVER_DICT[server]
        try:
            server_connected = other_server.connect()
            print('Connected to {} server.'.format(
                server_connected.friendlyName))
        except Exception as e:
            sys.stderr.write("Error: {}".format(e))
            sys.exit(1)

        main_section_dict = find_things(main_server)
        their_section_dict = find_things(server_connected)
        print('Comparing findings from {} and {}'.format(
            main_server.friendlyName, server_connected.friendlyName))
        main_dict = diff_things(main_section_dict, their_section_dict)
        # pop main keys
        main_dict.pop('movie', None)
        main_dict.pop('show', None)
        filename = 'diff_{}_{}_servers.json'.format(opts.server[0], server)

        with open(filename, 'w') as fp:
            json.dump(main_dict, fp, indent=4, sort_keys=True)
