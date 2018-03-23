"""
Create a Plex Playlist with what aired on this day in history (month-day), sort by oldest first.
If Playlist from yesterday exists delete and create today's.
If today's Playlist exists exit.
"""

import operator
from plexapi.server import PlexServer
import requests
import datetime

PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxxx'

LIBRARY_NAMES = ['Movies', 'TV Shows'] # Your library names

today = datetime.datetime.now().date()

TODAY_PLAY_TITLE = 'Aired Today {}-{}'.format(today.month, today.day)

plex = PlexServer(PLEX_URL, PLEX_TOKEN)

def remove_old():
    # Remove old Aired Today Playlists
    for playlist in plex.playlists():
        if playlist.title.startswith('Aired Today') and playlist.title != TODAY_PLAY_TITLE:
            playlist.delete()
            print('Removing old Aired Today Playlists: {}'.format(playlist.title))
        elif playlist.title == TODAY_PLAY_TITLE:
            print('{} already exists. No need to make again.'.format(TODAY_PLAY_TITLE))
            exit(0)


def get_all_content(library_name):
    # Get all movies or episodes from LIBRARY_NAME
    child_lst = []
    for library in library_name:
        for child in plex.library.section(library).all():
            if child.type == 'movie':
                child_lst += [child]
            elif child.type == 'show':
                child_lst += child.episodes()
            else:
                pass
    return child_lst


def find_air_dates(content_lst):
    # Find what aired with today's month-day
    aired_lst = []
    for video in content_lst:
        try:
            ad_month = str(video.originallyAvailableAt.month)
            ad_day = str(video.originallyAvailableAt.day)
            
            if ad_month == str(today.month) and ad_day == str(today.day):
                aired_lst += [[video] + [str(video.originallyAvailableAt)]]
        except Exception as e:
            # print(e)
            pass
        
        # Sort by original air date, oldest first
        aired_lst = sorted(aired_lst, key=operator.itemgetter(1))

    # Remove date used for sorting
    play_lst = [x[0] for x in aired_lst]
    return play_lst


remove_old()
play_lst = find_air_dates(get_all_content(LIBRARY_NAMES))
# Create Playlist
if play_lst:
    plex.createPlaylist(TODAY_PLAY_TITLE, play_lst)
else:
    print('Found nothing aired on this day in history.')
