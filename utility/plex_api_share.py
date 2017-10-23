'''
Share or unshare libraries.

optional arguments:
  -h, --help            show this help message and exit
  -s [], --share []     To share or to unshare.:
                        (choices: share, share_all, unshare)
  -u [], --user []      Space separated list of case sensitive names to process. Allowed names are:
                        (choices: All users names)
  -l  [ ...], --libraries  [ ...]
                        Space separated list of case sensitive names to process. Allowed names are:
                        (choices: All library names)
                        (default: All Libraries)

Usage:

   plex_api_share.py -s share -u USER -l Movies
       - Shared libraries: ['Movies'] with USER

   plex_api_share.py -s share -u USER -l Movies "TV Shows"
       - Shared libraries: ['Movies', 'TV Shows'] with USER
          * Double Quote libraries with spaces

   plex_api_share.py -s share_all -u USER
       - Shared all libraries with USER.

   plex_api_share.py -s unshare -u USER
       - Unshared all libraries with USER.
       - USER is still exists as a Friend or Home User

'''

from plexapi.server import PlexServer
import argparse

PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxxxx'
plex = PlexServer(PLEX_URL, PLEX_TOKEN)

user_lst = [x.title for x in plex.myPlexAccount().users()]
sections_lst = [x.title for x in plex.library.sections()]


def share(user, libraries):
    plex.myPlexAccount().updateFriend(user=user, server=plex, sections=libraries)
    print('Shared libraries: {libraries} with {user}.'.format(libraries=libraries, user=user))


def unshare(user, libraries):
    plex.myPlexAccount().updateFriend(user=user, server=plex, removeSections=True, sections=libraries)
    print('Unshared all libraries from {user}.'.format(libraries=libraries, user=user))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Share or unshare libraries.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-s', '--share', nargs='?', type=str, required=True,
                        choices=['share', 'share_all', 'unshare'], metavar='',
                        help='To share or to unshare.: \n (choices: %(choices)s)')
    parser.add_argument('-u', '--user', nargs='?', type=str, required=True, choices=user_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s)')
    parser.add_argument('-l', '--libraries', nargs='+', default='', choices=sections_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s \n(default: All Libraries)')

    opts = parser.parse_args()

    if opts.share == 'share':
        share(opts.user, opts.libraries)
    elif opts.share == 'unshare':
        unshare(opts.user, opts.libraries)
    elif opts.share == 'share_all':
        share(opts.user, sections_lst)
    else:
        print('I don\'t know what else you want.')
