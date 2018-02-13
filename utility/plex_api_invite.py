'''
Invite new users to share Plex libraries.

optional arguments:
  -h, --help            show this help message and exit
  -s [], --share []     Share specific libraries or share all libraries.
                        (choices: share, share_all)
  -u [], --user []      Enter a valid username(s) or email address(s) for user to be invited.
  -l  [ ...], --libraries  [ ...]
                        Space separated list of case sensitive names to process. Allowed names are:
                        (choices: All library names)
  --sync                Allow user to sync content
  --camera              Allow user to upload photos
  --channel             Allow user to utilize installed channels
  --movieRatings        Add rating restrictions to movie library types
  --movieLabels         Add label restrictions to movie library types
  --tvRatings           Add rating restrictions to show library types
  --tvLabels            Add label restrictions to show library types
  --musicLabels         Add label restrictions to music library types

Usage:

   plex_api_invite.py -s share -u USER -l Movies
       - Shared libraries: ['Movies'] with USER

   plex_api_invite.py -s share -u USER -l Movies "TV Shows"
       - Shared libraries: ['Movies', 'TV Shows'] with USER
          * Double Quote libraries with spaces

   plex_api_invite.py -s share_all -u USER
       - Shared all libraries with USER.

   plex_api_invite.py -s share Movies -u USER --movieRatings G, PG-13
       - Share Movie library with USER but restrict them to only G and PG-13 titles.

'''

from plexapi.server import PlexServer
import argparse
import requests

PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxxxx'

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

sections_lst = [x.title for x in plex.library.sections()]
ratings_lst = ['G', 'PG', 'PG-13', 'R', 'NC-17', 'TV-G', 'TV-Y', 'TV-Y7', 'TV-14', 'TV-PG', 'TV-MA']


def invite(user, sections, allowSync, camera, channels, filterMovies, filterTelevision, filterMusic):
    plex.myPlexAccount().inviteFriend(user=user, server=plex, sections=sections, allowSync=allowSync,
                                      allowCameraUpload=camera, allowChannels=channels, filterMovies=filterMovies,
                                      filterTelevision=filterTelevision, filterMusic=filterMusic)
    print('Invited {user} to share libraries: {libraries}.'.format(libraries=sections, user=user))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Invite new users to share Plex libraries.",
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-s', '--share', nargs='?', type=str, required=True,
                        choices=['share', 'share_all'], metavar='',
                        help='Share specific libraries or share all libraries.: \n (choices: %(choices)s)')
    parser.add_argument('-u', '--user', nargs='+', type=str, required=True, metavar='',
                        help='Enter a valid username(s) or email address(s) for user to be invited.')
    parser.add_argument('-l', '--libraries', nargs='+', default='', choices=sections_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s')

    parser.add_argument('--sync', default=False, action='store_true',
                        help='Use to allow user to sync content.')
    parser.add_argument('--camera', default=False, action='store_true',
                        help='Use to allow user to upload photos.')
    parser.add_argument('--channels', default=False, action='store_true',
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

    filterMovies = {}
    filterTelevision = {}
    filterMusic = {}

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

    for user in opts.user:
        if opts.share == 'share':
            invite(user, opts.libraries, opts.sync, opts.camera, opts.channels,
                   filterMovies, filterTelevision, filterMusic)
        elif opts.share == 'share_all':
            invite(user, sections_lst, opts.sync, opts.camera, opts.channels,
                   filterMovies, filterTelevision, filterMusic)
