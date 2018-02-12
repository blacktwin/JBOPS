'''
Build playlist from popular tracks.

optional arguments:
  -h, --help           show this help message and exit
  --name []            Name your playlist
  --libraries  [ ...]  Space separated list of case sensitive names to process. Allowed names are:
                       (choices: ALL MUSIC LIBRARIES)*
  --artists  [ ...]    Space separated list of case sensitive names to process. Allowed names are:
                       (choices: ALL ARTIST NAMES)
  --tracks []          Specify the track length you would like the playlist.
  --random []          Randomly select N artists.

* LIBRARY_EXCLUDE are excluded from libraries choice.

'''


import requests
from plexapi.server import PlexServer
import argparse
import random

# Edit
PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxxxx'

LIBRARY_EXCLUDE = ['Audio Books', 'Podcasts', 'Soundtracks']
DEFAULT_NAME = 'Popular Music Playlist'

# /Edit

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

music_sections = [x.title for x in plex.library.sections() if x.type == 'artist' and x.title not in LIBRARY_EXCLUDE]

artist_lst = []
for section in music_sections:
    artist_lst += [x.title.encode('utf-8') for x in plex.library.section(section).all() if section not in LIBRARY_EXCLUDE]


def fetch(path):
    url = PLEX_URL

    header = {'Accept': 'application/json'}
    params = {'X-Plex-Token': PLEX_TOKEN,
               'includePopularLeaves': '1'
               }

    r = requests.get(url + path, headers=header, params=params, verify=False)
    return r.json()['MediaContainer']['Metadata'][0]['PopularLeaves']['Metadata']


def build_tracks(music_lst):
    ratingKey_lst = []
    track_lst = []

    for artist in music_lst:
        try:
            ratingKey_lst += fetch('/library/metadata/{}'.format(artist.ratingKey))
            for tracks in ratingKey_lst:
                track_lst.append(plex.fetchItem(int(tracks['ratingKey'])))
        except KeyError as e:
            print('Artist: {} does not have any popular tracks listed.'.format(artist.title))
            print('Error: {}'.format(e))

    return track_lst


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Build playlist from popular tracks.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--name', nargs='?', default=DEFAULT_NAME, metavar='',
                        help='Name your playlist')
    parser.add_argument('--libraries', nargs='+', default=False, choices=music_sections, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s)')
    parser.add_argument('--artists', nargs='+', default=False, choices=artist_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s)')

    parser.add_argument('--tracks', nargs='?', default=False, type=int, metavar='',
                        help='Specify the track length you would like the playlist.')
    parser.add_argument('--random',nargs='?', default=False, type=int, metavar='',
                        help='Randomly select N artists.')

    opts = parser.parse_args()
    playlist = []

    if opts.libraries and not opts.artists and not opts.random:
        for section in opts.libraries:
            playlist += build_tracks(plex.library.section(section).all())

    elif opts.libraries and opts.artists and not opts.random:
        for artist in opts.artists:
            for section in opts.libraries:
                artist_objects = [x for x in plex.library.section(section).all() if x.title == artist]
                playlist += build_tracks(artist_objects)

    elif not opts.libraries and opts.artists and not opts.random:
        for artist in opts.artists:
            for section in music_sections:
                artist_objects = [x for x in plex.library.section(section).all() if x.title == artist]
                playlist += build_tracks(artist_objects)

    elif not opts.libraries and not opts.artists and opts.random:
        rand_artists = random.sample((artist_lst), opts.random)
        for artist in rand_artists:
            for section in music_sections:
                artist_objects = [x for x in plex.library.section(section).all() if x.title == artist]
                playlist += build_tracks(artist_objects)

    if opts.tracks and opts.random:
        playlist = random.sample((playlist), opts.tracks)
        
    elif opts.tracks and not opts.random:
        playlist = playlist[:opts.tracks]

    # Create Playlist
    plex.createPlaylist(opts.name, playlist)
