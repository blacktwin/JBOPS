#!/usr/bin/env python
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
server_lst = []

def find_things(server, media_type):
    dict_tt = {}
    print('Finding items from {}.'.format(server.friendlyName))
    for section in server.library.sections():
        if section.title not in IGNORE_LST and section.type in media_type:
            dict_tt[section.type] = []
            for item in server.library.section(section.title).all():
                dict_tt[section.type].append(server.fetchItem(item.ratingKey))

    return dict_tt


def org_diff(main, friend, key):
    diff_dict = {}

    shared = set(main + friend)
    print('... combining {}s'.format(key))

    mine = list(set(main) - set(friend))
    missing = list(set(friend) - set(main))
    combined = list(set(friend + main))
    diff_dict['{}_combined'.format(key)] = {'list': combined,
                                            'total': len(combined)}

    print('... comparing {}s'.format(key))
    print('... finding what is mine')
    diff_dict['{}_mine'.format(key)] = {'list': mine,
                                        'total': len(mine)}
    print('... finding what is missing')
    diff_dict['{}_missing'.format(key)] = {'list': missing,
                                           'total': len(missing)}
    print('... finding what is shared')
    ddiff = set(mine + missing)
    shared_lst = list(shared.union(ddiff) - shared.intersection(ddiff))
    diff_dict['{}_shared'.format(key)] = {'list': shared_lst,
                                          'total': len(shared_lst)}

    return diff_dict


def diff_things(main_dict, friend_dict):
    diff_dict = {}
    for key in main_dict.keys():
        main_titles = [x.title for x in main_dict[key]]
        friend_titles = [x.title for x in friend_dict[key]]
        diff_dict[key] = org_diff(main_titles, friend_titles, key)
        # todo-me guid double check?

    # todo-me check back to obj in main/friend for rating and bitrate weights

    return diff_dict


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Comparing content between two or more Plex servers.",
        formatter_class = argparse.RawTextHelpFormatter)
    parser.add_argument('--server', required=True, choices=SERVER_DICT.keys(),
                        action='append', nargs='?', metavar='',
                        help='Choose servers to connect to and compare.\n'
                             'Choices: (%(choices)s)')
    parser.add_argument('--media_type', required=True, choices=['movie', 'show', 'artist'],
                        nargs='+', metavar='', default=['movie', 'show'],
                        help='Choose media type(s) to compare.'
                             '\nDefault: (%(default)s)'
                             '\nChoices: (%(choices)s)')
    # todo-me add media_type [x], library_ignore[], media filters (genre, etc.) []

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
            server_lst.append(server_connected)
        except Exception as e:
            sys.stderr.write("Error: {}.\nSkipping...\n".format(e))
            pass

    if len(server_lst) == 0:
        sys.stderr.write("Need more than one server to compare.\n")
        sys.exit(1)

    main_section_dict = find_things(main_server, opts.media_type)

    for connection in server_lst:
        their_section_dict = find_things(connection, opts.media_type)
        print('Comparing findings from {} and {}'.format(
            main_server.friendlyName, connection.friendlyName))
        main_dict = diff_things(main_section_dict, their_section_dict)
        filename = 'diff_{}_{}_servers.json'.format(opts.server[0],
                                                    connection.friendlyName)

        with open(filename, 'w') as fp:
            json.dump(main_dict, fp, indent=4, sort_keys=True)
