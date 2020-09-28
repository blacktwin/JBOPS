#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description: Pull Playlists from Google Music and create Playlist in Plex
Author: Blacktwin, pjft, sdlynx
Requires: gmusicapi, plexapi, requests


 Example:

"""


from plexapi.server import PlexServer, CONFIG
from gmusicapi import Mobileclient

import requests
requests.packages.urllib3.disable_warnings()

PLEX_URL = ''
PLEX_TOKEN = ''
MUSIC_LIBRARY_NAME = 'Music'

## CODE BELOW ##

if not PLEX_URL:
    PLEX_URL = CONFIG.data['auth'].get('server_baseurl')
if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token')

# Connect to Plex Server
sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

# Connect to Google Music, if not authorized prompt to authorize
# See https://unofficial-google-music-api.readthedocs.io/en/latest/reference/mobileclient.html
# for more information
mc = Mobileclient()
if not mc.oauth_login(device_id=Mobileclient.FROM_MAC_ADDRESS):
    mc.perform_oauth()
GGMUSICLIST = mc.get_all_songs()
PLEX_MUSIC_LIBRARY = plex.library.section(MUSIC_LIBRARY_NAME)

def round_down(num, divisor):
    """
    Parameters
    ----------
    num (int,str): Number to round down
    divisor (int): Rounding digit

    Returns
    -------
    Rounded down int
    """
    num = int(num)
    return num - (num%divisor)


def compare(ggmusic, pmusic):
    """
    Parameters
    ----------
    ggmusic (dict): Contains track data from Google Music
    pmusic (object): Plex item found from search

    Returns
    -------
    pmusic (object): Matched Plex item
    """
    title = str(ggmusic['title'].encode('ascii', 'ignore'))
    album = str(ggmusic['album'].encode('ascii', 'ignore'))
    tracknum = int(ggmusic['trackNumber'])
    duration = int(ggmusic['durationMillis'])

    # Check if track numbers match
    if int(pmusic.index) == int(tracknum):
        return [pmusic]
    # If not track number, check track title and album title
    elif title == pmusic.title and (album == pmusic.parentTitle or
                                    album.startswith(pmusic.parentTitle)):
        return [pmusic]
    # Check if track duration match
    elif round_down(duration, 1000) == round_down(pmusic.duration, 1000):
        return [pmusic]
    # Lastly, check if title matches
    elif title == pmusic.title:
        return [pmusic]

def get_ggmusic(trackId):
    for ggmusic in GGMUSICLIST:
        if ggmusic['id'] == trackId:
            return ggmusic

def main():
    for pl in mc.get_all_user_playlist_contents():
        playlistName = pl['name']
        # Check for existing Plex Playlists, skip if exists
        if playlistName in [x.title for x in plex.playlists()]:
            print("Playlist: ({}) already available, skipping...".format(playlistName))
        else:
            playlistContent = []
            shareToken = pl['shareToken']
            # Go through tracks in Google Music Playlist
            for ggmusicTrackInfo in pl['tracks']:
                ggmusic = get_ggmusic(ggmusicTrackInfo['trackId'])
                title = str(ggmusic['title'])
                album = str(ggmusic['album'])
                artist = str(ggmusic['artist'])
                # Search Plex for Album title and Track title
                albumTrackSearch = PLEX_MUSIC_LIBRARY.searchTracks(
                        **{'album.title': album, 'track.title': title})
                # Check results
                if len(albumTrackSearch) == 1:
                    playlistContent += albumTrackSearch
                if len(albumTrackSearch) > 1:
                    for pmusic in albumTrackSearch:
                        albumTrackFound = compare(ggmusic, pmusic)
                        if albumTrackFound:
                            playlistContent += albumTrackFound
                            break
                # Nothing found from Album title and Track title
                if not albumTrackSearch or len(albumTrackSearch) == 0:
                    # Search Plex for Track title
                    trackSearch = PLEX_MUSIC_LIBRARY.searchTracks(
                            **{'track.title': title})
                    if len(trackSearch) == 1:
                        playlistContent += trackSearch
                    if len(trackSearch) > 1:
                        for pmusic in trackSearch:
                            trackFound = compare(ggmusic, pmusic)
                            if trackFound:
                                playlistContent += trackFound
                                break
                    # Nothing found from Track title
                    if not trackSearch or len(trackSearch) == 0:
                        # Search Plex for Artist
                        artistSearch = PLEX_MUSIC_LIBRARY.searchTracks(
                                **{'artist.title': artist})
                        for pmusic in artistSearch:
                            artistFound = compare(ggmusic, pmusic)
                            if artistFound:
                                playlistContent += artistFound
                                break
                        if not artistSearch or len(artistSearch) == 0:
                            print(u"Could not find in Plex:\n\t{} - {} {}".format(artist, album, title))
            if len(playlistContent) != 0:
                print("Adding Playlist: {}".format(playlistName))
                print("Google Music Playlist: {}, has {} tracks. {} tracks were added to Plex.".format(
                    playlistName, len(pl['tracks']), len(playlistContent)))
                plex.createPlaylist(playlistName, playlistContent)
            else:
                print("Could not find any matching tracks in Plex for {}".format(playlistName))

main()
