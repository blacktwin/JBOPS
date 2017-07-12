"""
Create a Plex Playlist with what was aired on this today's month-day, sort by oldest first.
If Playlist from yesterday exists delete and create today's.
If today's Playlist exists exit.
"""

import operator, time
from plexapi.server import PlexServer
import requests

baseurl = 'http://localhost:32400'
token = 'xxxxxx'
plex = PlexServer(baseurl, token)

library_name = ['Movies', 'TV Shows'] # You library names

child_lst = []
aired_lst = []

today = time.gmtime(time.time())

TODAY_PLAY_TITLE = 'Aired Today {}-{}'.format(today.tm_mon, today.tm_mday)

# Remove old Aired Today Playlists
for playlist in plex.playlists():
    if playlist.title == TODAY_PLAY_TITLE.startswith('Aired Today') and not TODAY_PLAY_TITLE:
        r = requests.delete('{}/playlists/{}?X-Plex-Token={}'
                    .format(baseurl, TODAY_PLAY_TITLE, token))
        print('Removing old Aired Today Playlists ')
        print(r)
    elif playlist.title == TODAY_PLAY_TITLE:
        print('{} already exists. No need to make again.'.format(TODAY_PLAY_TITLE))
        exit(0)

# Get all movies or episodes from LIBRARY_NAME
for library in library_name:
    for child in plex.library.section(library).all():
        if child.type == 'movie':
            child_lst += [child]
        elif child.type == 'show':
            child_lst += child.episodes()
        else:
            pass

# Find what aired with today's month-day
for video in child_lst:
    try:
        if str(video.originallyAvailableAt.month) == str(today.tm_mon) \
                and str(video.originallyAvailableAt.day) == str(today.tm_mday):
            aired_lst += [[video] + [str(video.originallyAvailableAt)]]
    except Exception as e:
        pass
    # Sort by original air date, oldest first
    aired_lst = sorted(aired_lst, key=operator.itemgetter(1))

# Remove date used for sorting
play_lst = [x[0] for x in aired_lst]

# Create Playlist
plex.createPlaylist(TODAY_PLAY_TITLE, play_lst)
