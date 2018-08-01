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
    dict_tt = {name: [] for name in media_type}
    print('Finding items from {}.'.format(server.friendlyName))
    for section in server.library.sections():
        if section.title not in IGNORE_LST and section.type in media_type:
            for item in server.library.section(section.title).all():
                dict_tt[section.type].append(server.fetchItem(item.ratingKey))

    return dict_tt


def get_meta(meta):

    meta_dict = {'title': meta.title,
                 'rating': meta.rating,
                 'genres': [x.tag for x in meta.genres],
                 'server': [meta._server.friendlyName]
                }
    if meta.guid:
        agent = meta.guid
        source_name = agent.split('://')[0].split('.')[-1]
        source_id = agent.split('://')[1].split('?')[0]
        meta_dict[source_name] = source_id

    return meta_dict


def org_diff(lst_dicts, media_type, main_server):

    diff_dict = {}
    seen = {}
    dupes = []
    missing = []
    unique = []

    for mtype in media_type:
        meta_lst = []
        print('...combining {}s'.format(mtype))
        for server_lst in lst_dicts:
            for item in server_lst[mtype]:
                if item.title not in seen:
                    seen[item.title] = 1
                    meta_lst.append(get_meta(item))
                else:
                    if seen[item.title] == 1:
                        dupes.append(item.title)
                        for meta in meta_lst:
                            if meta['title'] == item.title:
                                meta['server'].append(item._server.friendlyName)
                    seen[item.title] += 1

        meta_lst = sorted(meta_lst, key=lambda d: d['rating'],
                          reverse=True)
        diff_dict[mtype] = {'combined': {'count': len(meta_lst),
                                              'list': meta_lst}}

        print('...finding {}s missing from {}'.format(
            mtype, main_server))
        for item in meta_lst:
            if main_server not in item['server']:
                missing.append(item)
            elif main_server in item['server'] and len(item['server']) == 1:
                unique.append(item)
        diff_dict[mtype].update({'missing': {'count': len(missing),
                                        'list': missing}})

        print('...finding {}s unique to {}'.format(
            mtype, main_server))
        diff_dict[mtype].update({'unique': {'count': len(unique),
                                         'list': unique}})

    return diff_dict


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Comparing content between two or more Plex servers.",
        formatter_class = argparse.RawTextHelpFormatter)
    parser.add_argument('--server', required=True, choices=SERVER_DICT.keys(),
                        action='append', nargs='?', metavar='',
                        help='Choose servers to connect to and compare.\n'
                             'Choices: (%(choices)s)')
    parser.add_argument('--media_type', choices=['movie', 'show', 'artist'],
                        nargs='+', metavar='', default=['movie', 'show'],
                        help='Choose media type(s) to compare.'
                             '\nDefault: (%(default)s)'
                             '\nChoices: (%(choices)s)')
    # todo-me add media_type [x], library_ignore[], media filters (genre, etc.) []

    opts = parser.parse_args()
    combined_lst = []

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

    combined_lst.append(find_things(main_server, opts.media_type))

    servers = [server.friendlyName for server in server_lst]

    for connection in server_lst:
        combined_lst.append(find_things(connection, opts.media_type))

    print('Combining findings from {} and {}'.format(
        main_server.friendlyName, ' and '.join(servers)))

    main_dict = org_diff(combined_lst, opts.media_type, main_server.friendlyName)

    filename = 'diff_{}_{}_servers.json'.format(opts.server[0],'_'.join(servers))

    with open(filename, 'w') as fp:
        json.dump(main_dict, fp, indent=4, sort_keys=True)
