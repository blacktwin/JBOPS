#!/usr/bin/env python
'''
Share or unshare libraries.

optional arguments:
  -h, --help            show this help message and exit
  --share               To share libraries.
  --shared              Display user's share settings.
  --unshare             To unshare all libraries.
  --kill                Kill user's current stream(s). Include message to override default message
  --add                 Add additional libraries.
  --remove              Remove existing libraries.
  --user  [ ...]        Space separated list of case sensitive names to process. Allowed names are:
                        (choices: All users names)
  --allUsers            Select all users.
  --libraries  [ ...]
                        Space separated list of case sensitive names to process. Allowed names are:
                        (choices: All library names)
                        (default: All Libraries)
  --allLibraries        Select all libraries.
  --sync                Allow user to sync content
  --camera              Allow user to upload photos
  --channel             Allow user to utilize installed channels
  --movieRatings        Add rating restrictions to movie library types
  --movieLabels         Add label restrictions to movie library types
  --tvRatings           Add rating restrictions to show library types
  --tvLabels            Add label restrictions to show library types
  --musicLabels         Add label restrictions to music library types
  --backup              Backup share settings from json file
  --restore             Restore share settings from json file
                        Filename of json file to use.
                        (choices: %(json files found in cwd)s)

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

   plex_api_share.py --restore
       - Only restore all Plex user's shares and settings from backup json file

   plex_api_share.py --restore --user USER
       - Only restore USER's Plex shares and settings from backup json file


   Excluding;

   --user becomes excluded if --allUsers is set
   plex_api_share.py --share --allUsers --user USER --libraries Movies
       - Shared libraries: ['Movies' ]with USER1.
       - Shared libraries: ['Movies'] with USER2 ... all users but USER

   --libraries becomes excluded if --allLibraries is set
   plex_api_share.py --share -u USER --allLibraries --libraries Movies
       - Shared [all libraries but Movies] with USER.

'''

from plexapi.server import PlexServer, CONFIG
import time
import argparse
import requests
import os
import json

PLEX_URL = ''
PLEX_TOKEN = ''
PLEX_URL = CONFIG.data['auth'].get('server_baseurl', PLEX_URL)
PLEX_TOKEN = CONFIG.data['auth'].get('server_token', PLEX_TOKEN)

DEFAULT_MESSAGE = "Steam is being killed by admin."

json_check = sorted([f for f in os.listdir('.') if os.path.isfile(f) and
                     f.endswith(".json")], key=os.path.getmtime)

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

user_lst = [x.title for x in plex.myPlexAccount().users()]
sections_lst = [x.title for x in plex.library.sections()]
movies_keys = [x.key for x in plex.library.sections() if x.type == 'movie']
show_keys = [x.key for x in plex.library.sections() if x.type == 'show']

my_server_names = []
# Find all owners server names. For owners with multiple servers.
for res in plex.myPlexAccount().resources():
    if res.provides == 'server' and res.owned == True:
        my_server_names.append(res.name)


def get_ratings_lst(section_id):
    headers = {'Accept': 'application/json'}
    params = {'X-Plex-Token': PLEX_TOKEN}
    content = requests.get("{}/library/sections/{}/contentRating".format(PLEX_URL, section_id),
                           headers=headers, params=params)

    ratings_keys = content.json()['MediaContainer']['Directory']
    ratings_lst = [x['title'] for x in ratings_keys]
    return ratings_lst


def filter_clean(filter_type):
    clean = ''
    try:
        clean = dict(item.split("=") for item in filter_type.split("|"))
        for k, v in clean.items():
            labels = v.replace('%20', ' ')
            labels = labels.split('%2C')
            clean[k] = labels
    except Exception as e:
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
        'servers': []}

    for server in user_acct.servers:
        if server.name in my_server_names:
            sections = []
            for section in server.sections():
                if section.shared == True:
                    sections.append(section.title)
            user_backup['servers'].append({'serverName': server.name,
                                           'sections': sections,
                                           'sectionCount': len(sections)})

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
    print('Shared libraries: {sections} with {user}.'.format(sections=sections, user=user))
    print('Settings: Sync: {}, Camer Upload: {}, Channels: {}, Movie Filters: {}, TV Filters: {}, Music Filter: {}'.
          format(allowSync, camera, channels, filterMovies, filterTelevision, filterMusic))


def unshare(user, sections):
    plex.myPlexAccount().updateFriend(user=user, server=plex, removeSections=True, sections=sections)
    print('Unuser_shares all libraries from {user}.'.format(user=user))


if __name__ == "__main__":

    movie_ratings = []
    show_ratings = []
    for movie in movies_keys:
        movie_ratings += get_ratings_lst(movie)
    for show in show_keys:
        show_ratings += get_ratings_lst(show)

    timestr = time.strftime("%Y%m%d-%H%M%S")

    parser = argparse.ArgumentParser(description="Share or unshare libraries.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--share', default=False, action='store_true',
                        help='To share libraries.')
    parser.add_argument('--shared', default=False, action='store_true',
                        help='Display user\'s shared libraries.')
    parser.add_argument('--unshare', default=False, action='store_true',
                        help='To unshare all libraries.')
    parser.add_argument('--kill', default=False, nargs='?',
                        help='Kill user\'s current stream(s). Include message to override default message.')
    parser.add_argument('--add', default=False, action='store_true',
                        help='Add additional libraries.')
    parser.add_argument('--remove', default=False, action='store_true',
                        help='Remove existing libraries.')
    parser.add_argument('--user', nargs='+', choices=user_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s)')
    parser.add_argument('--allUsers', default=False, action='store_true',
                        help='Select all users.')
    parser.add_argument('--libraries', nargs='+', default=False, choices=sections_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s')
    parser.add_argument('--allLibraries', default=False, action='store_true',
                        help='Select all libraries.')
    parser.add_argument('--sync', default=False, action='store_true',
                        help='Use to allow user to sync content.')
    parser.add_argument('--camera', default=False, action='store_true',
                        help='Use to allow user to upload photos.')
    parser.add_argument('--channels', default=False, action='store_true',
                        help='Use to allow user to utilize installed channels.')
    parser.add_argument('--movieRatings', nargs='+', choices=list(set(movie_ratings)), metavar='',
                        help='Use to add rating restrictions to movie library types.\n'
                             'Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s')
    parser.add_argument('--movieLabels', nargs='+', metavar='',
                        help='Use to add label restrictions for movie library types.')
    parser.add_argument('--tvRatings', nargs='+', choices=list(set(show_ratings)), metavar='',
                        help='Use to add rating restrictions for show library types.\n'
                             'Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s')
    parser.add_argument('--tvLabels', nargs='+', metavar='',
                        help='Use to add label restrictions for show library types.')
    parser.add_argument('--musicLabels', nargs='+', metavar='',
                        help='Use to add label restrictions for music library types.')

    parser.add_argument('--backup', default=False, action='store_true',
                        help='Backup share settings from json file.')
    parser.add_argument('--restore', type = str, choices = json_check,
                        help='Restore share settings from json file.\n'
                             'Filename of json file to use.\n'
                             '(choices: %(choices)s)')

    opts = parser.parse_args()
    users = ''
    libraries = ''
    filterMovies = {}
    filterTelevision = {}
    filterMusic = {}

    # Setting additional share options
    if opts.movieLabels:
        filterMovies['label'] = opts.movieLabels
    if opts.movieRatings:
        filterMovies['contentRating'] = opts.movieRatings
    if opts.tvLabels:
        filterTelevision['label'] = opts.tvLabels
    if opts.tvRatings:
        filterTelevision['contentRating'] = opts.tvRatings
    if opts.musicLabels:
        filterMusic['label'] = opts.musicLabels

    # Defining users
    if opts.allUsers and not opts.user:
        users = user_lst
    elif not opts.allUsers and opts.user:
        users = opts.user
    elif opts.allUsers and opts.user:
        # If allUsers is used then any users listed will be excluded
        for user in opts.user:
            user_lst.remove(user)
            users = user_lst

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

    # Share, Unshare, Kill, Add, or Remove
    for user in users:
        user_shares = find_shares(user)
        if libraries:
            if opts.share:
                share(user, libraries, opts.sync, opts.camera, opts.channels, filterMovies, filterTelevision,
                      filterMusic)
            if opts.add and user_shares['sections']:
                libraries = libraries + user_shares['sections']
                libraries = list(set(libraries))
                share(user, libraries, opts.sync, opts.camera, opts.channels, filterMovies, filterTelevision,
                      filterMusic)
            if opts.remove and user_shares['sections']:
                libraries = [sect for sect in user_shares['sections'] if sect not in libraries]
                share(user, libraries, opts.sync, opts.camera, opts.channels, filterMovies, filterTelevision,
                      filterMusic)
        if opts.shared:
            user_json = json.dumps(user_shares, indent=4, sort_keys=True)
            print('Current share settings for {}: {}'.format(user, user_json))
        if opts.unshare and opts.kill:
            kill_session(user, opts.kill)
            time.sleep(3)
            unshare(user, sections_lst)
        elif opts.unshare:
            unshare(user, sections_lst)
        elif opts.kill:
            kill_session(user, opts.kill)

    if opts.backup:
        print('Backing up share information...')
        users_shares = []
        for user in user_lst:
            # print('...Found {}'.format(user))
            users_shares.append(find_shares(user))
        json_file = 'Plex_share_backup_{}.json'.format(timestr)
        with open(json_file, 'w') as fp:
            json.dump(users_shares, fp, indent=4, sort_keys=True)

    if opts.restore:
        print('Using existing .json to restore Plex shares.')
        with open(''.join(opts.restore)) as json_data:
            shares_file = json.load(json_data)
        for user in shares_file:
            for server in user['servers']:
                # If user arg is defined then abide, else restore all
                if users:
                    if user['title'] in users:
                        print('Restoring user {}\'s shares and settings...'.format(user['title']))
                        share(user['title'], server['sections'], user['allowSync'], user['camera'],
                              user['channels'], user['filterMovies'], user['filterTelevision'],
                              user['filterMusic'])
                else:
                    print('Restoring user {}\'s shares and settings...'.format(user['title']))
                    share(user['title'], server['sections'], user['allowSync'], user['camera'],
                          user['channels'], user['filterMovies'], user['filterTelevision'],
                          user['filterMusic'])