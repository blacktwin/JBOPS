'''
Share or unshare libraries.

optional arguments:
  -h, --help            show this help message and exit
  --share               To share libraries.
  --shared              Display user's shared libraries.
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

   Excluding;

   --user becomes excluded if --allUsers is set
   plex_api_share.py --share --allUsers --user USER --libraries Movies
       - Shared libraries: ['Movies' ]with USER1.
       - Shared libraries: ['Movies'] with USER2 ... all users but USER

   --libraries becomes excluded if --allLibraries is set
   plex_api_share.py --share -u USER --allLibraries --libraries Movies
       - Shared [all libraries but Movies] with USER.

'''

from plexapi.server import PlexServer
from time import sleep
import argparse
import requests
import json

PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxx'

DEFAULT_MESSAGE = "Steam is being killed by admin."


sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)


user_lst = [x.title for x in plex.myPlexAccount().users()]
sections_lst = [x.title for x in plex.library.sections()]
movies_keys = [x.key for x in plex.library.sections() if x.type == 'movie']
show_keys = [x.key for x in plex.library.sections() if x.type == 'show']


def get_ratings_lst(section_id):
    headers = {'Accept': 'application/json'}
    params = {'X-Plex-Token': PLEX_TOKEN}
    content = requests.get("{}/library/sections/{}/contentRating".format(PLEX_URL, section_id),
                           headers=headers, params=params)

    # print(json.dumps(content.json(), indent=4, sort_keys=True))
    ratings_keys = content.json()['MediaContainer']['Directory']
    ratings_lst = [x['title'] for x in ratings_keys]
    return ratings_lst


def find_shares(user):
    shared_lst = []
    account = plex.myPlexAccount()
    user_acct = account.user(user)
    shared_sections = user_acct.servers[0]

    for section in shared_sections.sections():
        if section.shared == True:
            shared_lst.append(section.title)

    return shared_lst


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


def unshare(user, sections):
    plex.myPlexAccount().updateFriend(user=user, server=plex, removeSections=True, sections=sections)
    print('Unshared all libraries from {user}.'.format(user=user))


if __name__ == "__main__":

    movie_ratings = []
    show_ratings = []
    for movie in movies_keys:
        movie_ratings += get_ratings_lst(movie)
    for show in show_keys:
        show_ratings += get_ratings_lst(show)

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
        shared = find_shares(user)
        if libraries:
            if opts.share:
                share(user, libraries, opts.sync, opts.camera, opts.channels, filterMovies, filterTelevision,
                      filterMusic)
            if opts.add:
                libraries = libraries + shared
                libraries = list(set(libraries))
                share(user, libraries, opts.sync, opts.camera, opts.channels, filterMovies, filterTelevision,
                      filterMusic)
            if opts.remove:
                libraries = [sect for sect in shared if sect not in libraries]
                share(user, libraries, opts.sync, opts.camera, opts.channels, filterMovies, filterTelevision,
                      filterMusic)
        if opts.shared:
            print('Current shares for {}: {}'.format(user, shared))
        if opts.unshare and opts.kill:
            kill_session(user, opts.kill)
            sleep(3)
            unshare(user, sections_lst)
        elif opts.unshare:
            unshare(user, sections_lst)
        elif opts.kill:
            kill_session(user, opts.kill)
