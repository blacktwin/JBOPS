#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Share or unshare libraries.

optional arguments:
  -h, --help            Show this help message and exit
  --share               To share libraries to user.
  --shared              Display user's share settings.
  --unshare             To unshare all libraries from user.
  --add                 Share additional libraries or enable settings to user.
  --remove              Remove shared libraries or disable settings from user.
  --user  [ ...]        Space separated list of case sensitive names to process. Allowed names are:
                        (choices: All users names)
  --allUsers            Select all users.
  --libraries  [ ...]
                        Space separated list of case sensitive names to process. Allowed names are:
                        (choices: All library names)
                        (default: All Libraries)
  --allLibraries        Select all libraries.
  --backup              Backup share settings from json file
  --restore             Restore share settings from json file
                        Filename of json file to use.
                        (choices: %(json files found in cwd)s)
  --libraryShares       Show all shares by library

  # Plex Pass member only settings:
  --kill                Kill user's current stream(s). Include message to override default message
  --sync                Allow user to sync content
  --camera              Allow user to upload photos
  --channel             Allow user to utilize installed channels
  --movieRatings        Add rating restrictions to movie library types
  --movieLabels         Add label restrictions to movie library types
  --tvRatings           Add rating restrictions to show library types
  --tvLabels            Add label restrictions to show library types
  --musicLabels         Add label restrictions to music library types

Usage:

   plex_api_share.py --user USER --shared
       - Current shares for USER: ['Movies', 'Music']

   plex_api_share.py --share --user USER --libraries Movies
       - Shared libraries: ['Movies'] with USER

   plex_api_share.py --share --allUsers --libraries Movies
       - Shared libraries: ['Movies'] with USER
       - Shared libraries: ['Movies'] with USER1 ...

   plex_api_share.py --share --user USER --libraries Movies "TV Shows"
       - Shared libraries: ['Movies', 'TV Shows'] with USER
          * Double Quote libraries with spaces

   plex_api_share.py --share --user USER --allLibraries
       - Shared all libraries with USER.

   plex_api_share.py --user USER --add --libraries Movies
       - Adds Movies library share to USER

   plex_api_share.py  --allUsers --remove --libraries Movies
       - Removes Movies library share from all Users

   plex_api_share.py --unshare --user USER
       - Unshared all libraries with USER.
       - USER is still exists as a Friend or Home User

   plex_api_share.py --backup
       - Backup all user shares to a json file

   plex_api_share.py --backup --user USER
       - Backup USER shares to a json file

   plex_api_share.py --restore
       - Only restore all Plex user's shares and settings from backup json file

   plex_api_share.py --restore --user USER
       - Only restore USER's Plex shares and settings from backup json file

   plex_api_share.py --user USER --add --sync
       - Enable sync feature for USER

   plex_api_share.py --user USER --remove --sync
       - Disable sync feature for USER

   plex_api_share.py --libraryShares
       - {Library Name} is shared to the following users:
             {USERS}

   Excluding;

   --user becomes excluded if --allUsers is set
   plex_api_share.py --share --allUsers --user USER --libraries Movies
       - Shared libraries: ['Movies' ]with USER1.
       - Shared libraries: ['Movies'] with USER2 ... all users but USER

   --libraries becomes excluded if --allLibraries is set
   plex_api_share.py --share -u USER --allLibraries --libraries Movies
       - Shared [all libraries but Movies] with USER.

"""
from __future__ import print_function
from __future__ import unicode_literals

from plexapi.server import PlexServer, CONFIG
import time
import argparse
import requests
import os
import json

PLEX_URL = ''
PLEX_TOKEN = ''

if not PLEX_URL:
    PLEX_URL = CONFIG.data['auth'].get('server_baseurl', '')

if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token', '')

DEFAULT_MESSAGE = "Stream is being killed by admin."

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

user_lst = {x.title: x.email if x.email else x.title for x in plex.myPlexAccount().users() if x.title}
user_choices = list(set(user_lst.values())) + list(user_lst.keys())
sections_lst = [x.title for x in plex.library.sections()]
movies_keys = [x.key for x in plex.library.sections() if x.type == 'movie']
show_keys = [x.key for x in plex.library.sections() if x.type == 'show']

json_check = sorted([f for f in os.listdir('.') if os.path.isfile(f) and
                     f.endswith(".json") and
                     f.startswith(plex.friendlyName)],
                    key=os.path.getmtime)

my_server_names = []
# Find all owners server names. For owners with multiple servers.
for res in plex.myPlexAccount().resources():
    if res.provides == 'server' and res.owned is True:
        my_server_names.append(res.name)

ALLOWED_MEDIA_FILTERS = ('contentRating', 'contentRating!', 'label', 'label!')


def get_ratings_lst(section_id):
    headers = {'Accept': 'application/json'}
    params = {'X-Plex-Token': PLEX_TOKEN}
    content = sess.get("{}/library/sections/{}/contentRating".format(PLEX_URL, section_id),
                       headers=headers, params=params)

    try:
        ratings_keys = content.json()['MediaContainer']['Directory']
        ratings_lst = [x['title'] for x in ratings_keys]
        return ratings_lst
    except Exception:
        print("Unable to pull ratings from section ID: {}.".format(section_id))
        pass


def filter_clean(filter_type):
    clean = ''
    try:
        filter_type = filter_type.replace('|', '&')
        clean = dict(item.split("=") for item in filter_type.split("&"))
        for k, v in clean.items():
            labels = v.replace('%20', ' ')
            labels = labels.split('%2C')
            clean[k] = labels
    except Exception:
        pass
    return clean


def find_shares(user):
    account = plex.myPlexAccount()
    user_acct = account.user(user)

    user_backup = {
        'title': user_acct.title,
        'username': user_acct.username,
        'email': user_acct.email,
        'userID': user_acct.id,
        'allowSync': user_acct.allowSync,
        'camera': user_acct.allowCameraUpload,
        'channels': user_acct.allowChannels,
        'filterMovies': filter_clean(user_acct.filterMovies),
        'filterTelevision': filter_clean(user_acct.filterTelevision),
        'filterMusic': filter_clean(user_acct.filterMusic),
        'serverName': plex.friendlyName,
        'sections': ""}

    for server in user_acct.servers:
        if server.name == plex.friendlyName:
            sections = []
            for section in server.sections():
                if section.shared is True:
                    sections.append(section.title)
            user_backup['sections'] = sections

    return user_backup


def kill_session(user, message):
    reason = DEFAULT_MESSAGE
    for session in plex.sessions():
        # Check for users stream
        if session.usernames[0] in user:
            title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            print('{user} was watching {title}. Killing stream and unsharing.'.format(
                user=user, title=title))
            if message:
                reason = message
            session.stop(reason=reason)


def share(user, sections, allowSync, camera, channels, filterMovies, filterTelevision, filterMusic):
    plex.myPlexAccount().updateFriend(user=user, server=plex, sections=sections, allowSync=allowSync,
                                      allowCameraUpload=camera, allowChannels=channels, filterMovies=filterMovies,
                                      filterTelevision=filterTelevision, filterMusic=filterMusic)
    if sections:
        print('{user}\'s updated shared libraries: \n{sections}'.format(sections=sections, user=user))
    if allowSync is True:
        print('Sync: Enabled')
    if allowSync is False:
        print('Sync: Disabled')
    if camera is True:
        print('Camera Upload: Enabled')
    if camera is False:
        print('Camera Upload: Disabled')
    if channels is True:
        print('Plugins: Enabled')
    if channels is False:
        print('Plugins: Disabled')
    if filterMovies:
        print('Movie Filters: {}'.format(filterMovies))
    if filterMovies == {}:
        print('Movie Filters:')
    if filterTelevision:
        print('Show Filters: {}'.format(filterTelevision))
    if filterTelevision == {}:
        print('Show Filters:')
    if filterMusic:
        print('Music Filters: {}'.format(filterMusic))
    if filterMusic == {} and filterMusic is not None:
        print('Music Filters:')


def unshare(user, sections):
    plex.myPlexAccount().updateFriend(user=user, server=plex, removeSections=True, sections=sections)
    print('Unshared all libraries from {user}.'.format(user=user))


def add_to_dictlist(d, key, val):
    if key not in d:
        d[key] = [val]
    else:
        d[key].append(val)
        

def allowed_filters(filters, filterDict):
    for filter in filters[0]:
        if filter[0] in ALLOWED_MEDIA_FILTERS:
            add_to_dictlist(filterDict, filter[0], filter[1])
        else:
            print("{} is not among the allowed keys for this argument.\n"
                  "Allowed keys: {}".format(filter[0], ','.join(ALLOWED_MEDIA_FILTERS)))
        

if __name__ == "__main__":

    timestr = time.strftime("%Y%m%d-%H%M%S")

    parser = argparse.ArgumentParser(description="Share or unshare libraries.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--share', default=False, action='store_true',
                        help='To share libraries.')
    parser.add_argument('--shared', default=False, action='store_true',
                        help='Display user\'s shared libraries.')
    parser.add_argument('--unshare', default=False, action='store_true',
                        help='To unshare all libraries.')
    parser.add_argument('--add', default=False, action='store_true',
                        help='Share additional libraries or enable settings to user..')
    parser.add_argument('--remove', default=False, action='store_true',
                        help='Remove shared libraries or disable settings from user.')
    parser.add_argument('--user', nargs='+', choices=user_choices, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s)')
    parser.add_argument('--allUsers', default=False, action='store_true',
                        help='Select all users.')
    parser.add_argument('--libraries', nargs='+', default=False, choices=sections_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s')
    parser.add_argument('--allLibraries', default=False, action='store_true',
                        help='Select all libraries.')
    parser.add_argument('--backup', default=False, action='store_true',
                        help='Backup share settings from json file.')
    parser.add_argument('--restore', type=str, choices=json_check, metavar='',
                        help='Restore share settings from json file.\n'
                             'Filename of json file to use.\n'
                             '(choices: %(choices)s)')
    parser.add_argument('--libraryShares', default=False, action='store_true',
                        help='Show all shares by library.')

    # For Plex Pass members
    if plex.myPlexSubscription is True:
        movie_ratings = []
        show_ratings = []
        for movie in movies_keys:
            ratings = get_ratings_lst(movie)
            if ratings: movie_ratings += ratings
        for show in show_keys:
            ratings = get_ratings_lst(show)
            if ratings: show_ratings += ratings
        parser.add_argument('--kill', default=None, nargs='?',
                            help='Kill user\'s current stream(s). Include message to override default message.')
        parser.add_argument('--sync', default=None, action='store_true',
                            help='Use to allow user to sync content.')
        parser.add_argument('--camera', default=None, action='store_true',
                            help='Use to allow user to upload photos.')
        parser.add_argument('--channels', default=None, action='store_true',
                            help='Use to allow user to utilize installed channels.')
        parser.add_argument('--movieRatings', nargs='+', choices=list(set(movie_ratings)), metavar='',
                            help='Use to add rating restrictions to movie library types.\n'
                                 'Space separated list of case sensitive names to process. Allowed names are: \n'
                                 '(choices: %(choices)s')
        parser.add_argument('--movieLabels', nargs='+', action='append', type=lambda kv: kv.split("="),
                            help='Use to add label restrictions for movie library types.')
        parser.add_argument('--tvRatings', nargs='+', choices=list(set(show_ratings)), metavar='',
                            help='Use to add rating restrictions for show library types.\n'
                                 'Space separated list of case sensitive names to process. Allowed names are: \n'
                                 '(choices: %(choices)s')
        parser.add_argument('--tvLabels', nargs='+', action='append', type=lambda kv: kv.split("="),
                            help='Use to add label restrictions for show library types.')
        parser.add_argument('--musicLabels', nargs='+', metavar='',
                            help='Use to add label restrictions for music library types.')

    opts = parser.parse_args()
    users = ''
    libraries = ''

    # Plex Pass additional share options
    kill = None
    sync = None
    camera = None
    channels = None
    filterMovies = None
    filterTelevision = None
    filterMusic = None
    try:
        if opts.kill:
            kill = opts.kill
        if opts.sync:
            sync = opts.sync
        if opts.camera:
            camera = opts.camera
        if opts.channels:
            channels = opts.channels
        if opts.movieLabels or opts.movieRatings:
            filterMovies = {}
        if opts.movieLabels:
            allowed_filters(opts.movieLabels, filterMovies)
        if opts.movieRatings:
            allowed_filters(opts.movieRatings, filterMovies)
        if opts.tvLabels or opts.tvRatings:
            filterTelevision = {}
        if opts.tvLabels:
            allowed_filters(opts.tvLabels, filterTelevision)
        if opts.tvRatings:
            allowed_filters(opts.tvRatings, filterTelevision)
        if opts.musicLabels:
            filterMusic = {}
            allowed_filters(opts.musicLabels, filterMusic)
    except AttributeError:
        print('No Plex Pass moving on...')

    # Defining users
    if opts.allUsers and not opts.user:
        users = user_lst.keys()
    elif not opts.allUsers and opts.user:
        users = opts.user
    elif opts.allUsers and opts.user:
        # If allUsers is used then any users listed will be excluded
        for user in opts.user:
            # If username is used then remove
            if user_lst.get(user):
                del user_lst[user]
            # Else email is used and must find it's corresponding username and remove
            else:
                for k, v in user_lst.items():
                    if v == user:
                        del user_lst[k]

        users = user_lst.keys()

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

    if opts.libraryShares:
        users = user_lst.keys()
        user_sections = {}
        for user in users:
            user_shares_lst = find_shares(user)
            user_sections[user] = user_shares_lst['sections']

        section_users = {}
        for user, sections in user_sections.items():
            for section in sections:
                section_users.setdefault(section, []).append(user)

        for section, users in section_users.items():
            print("{} is shared to the following users:\n  {}\n".format(section, ", ".join(users)))
        exit()

    # Share, Unshare, Kill, Add, or Remove
    for user in users:
        user_shares = find_shares(user)
        user_shares_lst = user_shares['sections']
        if libraries:
            if opts.share:
                share(user, libraries, sync, camera, channels, filterMovies, filterTelevision,
                      filterMusic)
            if opts.add and user_shares_lst:
                addedLibraries = libraries + user_shares_lst
                addedLibraries = list(set(addedLibraries))
                share(user, addedLibraries, sync, camera, channels, filterMovies, filterTelevision,
                      filterMusic)
            if opts.remove and user_shares_lst:
                removedLibraries = [sect for sect in user_shares_lst if sect not in libraries]
                share(user, removedLibraries, sync, camera, channels, filterMovies, filterTelevision,
                      filterMusic)
        else:
            if opts.add:
                # Add/Enable settings independently of libraries
                addedLibraries = user_shares_lst
                share(user, addedLibraries, sync, camera, channels, filterMovies, filterTelevision,
                      filterMusic)
            if opts.remove:
                # Remove/Disable settings independently of libraries
                # If remove and setting arg is True then flip setting to false to disable
                if sync:
                    sync = False
                if camera:
                    camera = False
                if channels:
                    channels = False
                # Filters are cleared
                # todo-me clear completely or pop arg values?
                if filterMovies:
                    filterMovies = {}
                if filterTelevision:
                    filterTelevision = {}
                if filterMusic:
                    filterMusic = {}
                share(user, libraries, sync, camera, channels, filterMovies, filterTelevision,
                      filterMusic)

        if opts.shared:
            user_json = json.dumps(user_shares, indent=4, sort_keys=True)
            print('Current share settings for {}: {}'.format(user, user_json))
        if opts.unshare and kill:
            kill_session(user, kill)
            time.sleep(3)
            unshare(user, sections_lst)
        elif opts.unshare and user_shares_lst:
            unshare(user, sections_lst)
        elif opts.unshare and not user_shares_lst:
            print('{} has no libraries shared...'.format(user))
        elif kill:
            kill_session(user, kill)

    if opts.backup:
        print('Backing up share information...')
        users_shares = []
        # If user arg is defined then abide, else backup all
        if not users:
            users = user_lst
        for user in users:
            # print('...Found {}'.format(user))
            users_shares.append(find_shares(user))
        json_file = '{}_Plex_share_backup_{}.json'.format(plex.friendlyName, timestr)
        with open(json_file, 'w') as fp:
            json.dump(users_shares, fp, indent=4, sort_keys=True)

    if opts.restore:
        print('Using existing .json to restore Plex shares.')
        with open(''.join(opts.restore)) as json_data:
            shares_file = json.load(json_data)
        for user in shares_file:
            # If user arg is defined then abide, else restore all
            if users:
                if user['title'] in users:
                    print('Restoring user {}\'s shares and settings...'.format(user['title']))
                    share(user['title'], user['sections'], user['allowSync'], user['camera'],
                          user['channels'], user['filterMovies'], user['filterTelevision'],
                          user['filterMusic'])
            else:
                print('Restoring user {}\'s shares and settings...'.format(user['title']))
                share(user['title'], user['sections'], user['allowSync'], user['camera'],
                      user['channels'], user['filterMovies'], user['filterTelevision'],
                      user['filterMusic'])
