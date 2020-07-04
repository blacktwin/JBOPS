#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Invite new users to share Plex libraries.

optional arguments:
  -h, --help            show this help message and exit
  --user []             Enter a valid username(s) or email address(s) for user to be invited.
  --libraries  [ ...]
                        Space separated list of case sensitive names to process. Allowed names are:
                        (choices: All library names)
  --allLibraries        Select all libraries.
  --sync                Allow user to sync content
  --camera              Allow user to upload photos
  --channel             Allow user to utilize installed channels
  --movieRatings        Add rating restrictions to movie library types
  --movieLabels         Add label restrictions to movie library types
  --tvRatings           Add rating restrictions to show library types
  --tvLabels            Add label restrictions to show library types
  --musicLabels         Add label restrictions to music library types

Usage:

   plex_api_invite.py --user USER --libraries Movies
       - Shared libraries: ['Movies'] with USER

   plex_api_invite.py --user USER --libraries Movies "TV Shows"
       - Shared libraries: ['Movies', 'TV Shows'] with USER
          * Double Quote libraries with spaces

   plex_api_invite.py --allLibraries --user USER
       - Shared all libraries with USER.

   plex_api_invite.py --libraries Movies --user USER --movieRatings G, PG-13
       - Share Movie library with USER but restrict them to only G and PG-13 titles.

"""
from __future__ import print_function
from __future__ import unicode_literals

from plexapi.server import PlexServer, CONFIG
import argparse
import requests

PLEX_URL = ''
PLEX_TOKEN = ''

if not PLEX_URL:
    PLEX_URL = CONFIG.data['auth'].get('server_baseurl', '')

if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token', '')

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

sections_lst = [x.title for x in plex.library.sections()]
ratings_lst = ['G', 'PG', 'PG-13', 'R', 'NC-17', 'TV-G', 'TV-Y', 'TV-Y7', 'TV-14', 'TV-PG', 'TV-MA']


def invite(user, sections, allowSync, camera, channels, filterMovies, filterTelevision, filterMusic):
    plex.myPlexAccount().inviteFriend(user=user, server=plex, sections=sections, allowSync=allowSync,
                                      allowCameraUpload=camera, allowChannels=channels, filterMovies=filterMovies,
                                      filterTelevision=filterTelevision, filterMusic=filterMusic)
    print('Invited {user} to share libraries: \n{sections}'.format(sections=sections, user=user))
    if allowSync is True:
        print('Sync: Enabled')
    if camera is True:
        print('Camera Upload: Enabled')
    if channels is True:
        print('Plugins: Enabled')
    if filterMovies:
        print('Movie Filters: {}'.format(filterMovies))
    if filterTelevision:
        print('Show Filters: {}'.format(filterTelevision))
    if filterMusic:
        print('Music Filters: {}'.format(filterMusic))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Invite new users to share Plex libraries.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--user', nargs='+', required=True,
                        help='Enter a valid username(s) or email address(s) for user to be invited.')
    parser.add_argument('--libraries', nargs='+', default=False, choices=sections_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s')
    parser.add_argument('--allLibraries', default=False, action='store_true',
                        help='Select all libraries.')
    parser.add_argument('--sync', default=None, action='store_true',
                        help='Use to allow user to sync content.')
    parser.add_argument('--camera', default=None, action='store_true',
                        help='Use to allow user to upload photos.')
    parser.add_argument('--channels', default=None, action='store_true',
                        help='Use to allow user to utilize installed channels.')
    parser.add_argument('--movieRatings', nargs='+', choices=ratings_lst, metavar='',
                        help='Use to add rating restrictions to movie library types.')
    parser.add_argument('--movieLabels', nargs='+',
                        help='Use to add label restrictions for movie library types.')
    parser.add_argument('--tvRatings', nargs='+', choices=ratings_lst, metavar='',
                        help='Use to add rating restrictions for show library types.')
    parser.add_argument('--tvLabels', nargs='+',
                        help='Use to add label restrictions for show library types.')
    parser.add_argument('--musicLabels', nargs='+',
                        help='Use to add label restrictions for music library types.')

    opts = parser.parse_args()
    libraries = ''

    # Plex Pass additional share options
    sync = None
    camera = None
    channels = None
    filterMovies = None
    filterTelevision = None
    filterMusic = None
    try:
        if opts.sync:
            sync = opts.sync
        if opts.camera:
            camera = opts.camera
        if opts.channels:
            channels = opts.channels
        if opts.movieLabels or opts.movieRatings:
            filterMovies = {}
        if opts.movieLabels:
            filterMovies['label'] = opts.movieLabels
        if opts.movieRatings:
            filterMovies['contentRating'] = opts.movieRatings
        if opts.tvLabels or opts.tvRatings:
            filterTelevision = {}
        if opts.tvLabels:
            filterTelevision['label'] = opts.tvLabels
        if opts.tvRatings:
            filterTelevision['contentRating'] = opts.tvRatings
        if opts.musicLabels:
            filterMusic = {}
            filterMusic['label'] = opts.musicLabels
    except AttributeError:
        print('No Plex Pass moving on...')

    # Defining libraries
    if opts.allLibraries and not opts.libraries:
        libraries = sections_lst
    elif not opts.allLibraries and opts.libraries:
        libraries = opts.libraries
    elif opts.allLibraries and opts.libraries:
        # If allLibraries is used then any libraries listed will be excluded
        for library in opts.libraries:
            sections_lst.remove(library)
            libraries = sections_lst

    for user in opts.user:
        invite(user, libraries, sync, camera, channels,
               filterMovies, filterTelevision, filterMusic)
