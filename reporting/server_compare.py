#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description: Comparing content between two or more Plex servers.
              Creates .json file in script directory of server compared.
              .json file contents include:
                  items by media types (movie, show)
                      items found in server 1, server 2, etc
                      items unique to server 1
                      items missing from server 1
Author: Blacktwin
Requires: requests, plexapi

 Example:
    python find_diff_other_servers.py --server "My Plex Server" --server PlexServer2
    python find_diff_other_servers.py --server "My Plex Server" --server PlexServer2 --server "Steven Plex"

"""
from __future__ import print_function
from __future__ import unicode_literals

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
    """Get all items based on media type

    Parameters
    ----------
    server: Object
        plexServerObject
    media_type: list
        ['movie', 'show', ..]

    Returns
    -------
    dictionary
        {media_type:[plexObject, ..]}

    """

    dict_tt = {name: [] for name in media_type}
    print('Finding items from {}.'.format(server.friendlyName))
    for section in server.library.sections():
        if section.title not in IGNORE_LST and section.type in media_type:
            for item in server.library.section(section.title).all():
                dict_tt[section.type].append(server.fetchItem(item.ratingKey))

    return dict_tt


def get_meta(meta):
    """Get metadata from Plex item.
    Parameters
    ----------
    meta: Object
        plexObject
    Returns
    -------
    dictionary
        {
        "genres": [],
        "imdb": "tt5158522",
        "rating": float,
        "server": ["Plex Server Name"],
        "title": "Title"
        }
    """
    thumb_url = '{}{}?X-Plex-Token={}'.format(
        meta._server._baseurl, meta.thumb, meta._server._token)

    meta_dict = {'title': meta.title,
                 'rating': meta.rating if
                 meta.rating is not None else 0.0,
                 'genres': [x.tag for x in meta.genres],
                 'server': [meta._server.friendlyName],
                 'thumb': [thumb_url]
                 }
    if meta.guid:
        # guid will return (com.plexapp.agents.imdb://tt4302938?lang=en)
        # Agents will differ between servers.
        agent = meta.guid
        source_name = agent.split('://')[0].split('.')[-1]
        source_id = agent.split('://')[1].split('?')[0]
        meta_dict[source_name] = source_id

    if meta.type == 'movie':
        # For movies with same titles
        meta_dict['title'] = u'{} ({})'.format(meta.title, meta.year)
    return meta_dict


def org_diff(lst_dicts, media_type, main_server):
    """Organizing the items from each server

    Parameters
    ----------
    media_type: list
        ['movie', 'show',..]
    lst_dicts: list
        [{media_type:[plexObject, ..]}, {media_type: [..]}]
    main_server: str
        'Plex Server Name'

    Returns
    -------
    nested dictionary
        media_type: {combined :{
                                list: [
                                {
                                    "genres": [],
                                    "imdb": "tt2313197",
                                    "rating": float,
                                    "server": ["Plex Server Name"],
                                    "title": ""
                                    },
                                ],
                                count: int
                                },
                    missing: {..}
                    unique: {..}
                    }
    """
    diff_dict = {}
    # todo-me pull posters from connected servers

    for mtype in media_type:
        meta_lst = []
        seen = {}
        missing = []
        unique = []
        print('...combining {}s'.format(mtype))
        for server_lst in lst_dicts:
            for item in server_lst[mtype]:
                if mtype == 'movie':
                    title = u'{} ({})'.format(item.title, item.year)
                else:
                    title = item.title

                # Look for duplicate titles
                if title not in seen:
                    seen[title] = 1
                    meta_lst.append(get_meta(item))
                else:
                    # Duplicate found
                    if seen[title] >= 1:
                        # Go back through list to find original
                        for meta in meta_lst:
                            if meta['title'] == title:
                                # Append the duplicate server's name
                                meta['server'].append(item._server.friendlyName)
                                thumb_url = '{}{}?X-Plex-Token={}'.format(
                                    item._server._baseurl, item.thumb, item._server._token)
                                meta['thumb'].append(thumb_url)
                    seen[title] += 1
        # Sort item list by Plex rating
        # Duplicates will use originals rating
        meta_lst = sorted(meta_lst, key=lambda d: d['rating'], reverse=True)
        diff_dict[mtype] = {'combined': {
            'count': len(meta_lst),
            'list': meta_lst}}

        print('...finding {}s missing from {}'.format(
            mtype, main_server))
        for item in meta_lst:
            # Main Server name is alone in items server list
            if main_server not in item['server']:
                missing.append(item)
            # Main Server name is absent in items server list
            elif main_server in item['server'] and len(item['server']) == 1:
                unique.append(item)
        diff_dict[mtype].update({'missing': {
            'count': len(missing),
            'list': missing}})

        print('...finding {}s unique to {}'.format(
            mtype, main_server))
        diff_dict[mtype].update({'unique': {
            'count': len(unique),
            'list': unique}})

    return diff_dict


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Comparing content between two or more Plex servers.",
        formatter_class=argparse.RawTextHelpFormatter)
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
    # First server in args is main server.
    main_server = server_compare.connect()
    print('Connected to {} server.'.format(main_server.friendlyName))

    for server in opts.server[1:]:
        other_server = SERVER_DICT[server]
        # Attempt to connect to other servers
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

    filename = 'diff_{}_{}_servers.json'.format(
        opts.server[0], '_'.join(servers))

    with open(filename, 'w') as fp:
        json.dump(main_dict, fp, indent=4, sort_keys=True)
