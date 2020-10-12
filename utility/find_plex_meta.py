#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Find location of Plex metadata.

find_plex_meta.py -s adventure
    pulls all titles with adventure in the title
or
find_plex_meta.py -s adventure -m movie
    pulls all movie titles with adventure in the title
'''
from __future__ import print_function
from __future__ import unicode_literals


from plexapi.server import PlexServer, CONFIG
# pip install plexapi
import os
import re
import hashlib
import argparse
import requests

# ## Edit ##
PLEX_URL = ''
PLEX_TOKEN = ''
PLEX_URL = CONFIG.data['auth'].get('server_baseurl', PLEX_URL)
PLEX_TOKEN = CONFIG.data['auth'].get('server_token', PLEX_TOKEN)
# Change directory based on your os see:
# https://support.plex.tv/hc/en-us/articles/202915258-Where-is-the-Plex-Media-Server-data-directory-located-
PLEX_LOCAL_TV_PATH = os.path.join(os.getenv('LOCALAPPDATA'), 'Plex Media Server\Metadata\TV Shows')
PLEX_LOCAL_MOVIE_PATH = os.path.join(os.getenv('LOCALAPPDATA'), 'Plex Media Server\Metadata\Movies')
PLEX_LOCAL_ALBUM_PATH = os.path.join(os.getenv('LOCALAPPDATA'), 'Plex Media Server\Metadata\Albums')
# ## /Edit ##

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


def hash_to_path(hash_str, path, title, media_type, artist=None):
    full_hash = hashlib.sha1(hash_str).hexdigest()
    hash_path = '{}\{}{}'.format(full_hash[0], full_hash[1::1], '.bundle')
    full_path = os.path.join(path, hash_path, 'Contents')
    if artist:
        output = "{}'s {} titled: {}\nPath: {}".format(artist, media_type, title, full_path)
    else:
        output = "{} titled: {}\nPath: {}".format(media_type.title(), title, full_path)
    print(output)


def get_plex_hash(search, mediatype=None):
    for searched in plex.search(search, mediatype=mediatype):
        # Need to find guid.
        if searched.type == 'show':
            # Get tvdb_if from first episode
            db_id = searched.episodes()[0].guid
            # Find str to pop
            str_pop = '/{}'.format(re.search(r'\/(.*)\?', db_id.split('//')[1]).group(1))
            # Create string to hash
            hash_str = db_id.replace(str_pop, '')
            hash_to_path(hash_str, PLEX_LOCAL_TV_PATH, searched.title, searched.type)

        elif searched.type == 'movie':
            # Movie guid is good to hash
            hash_to_path(searched.guid, PLEX_LOCAL_MOVIE_PATH, searched.title, searched.type)

        elif searched.type == 'album':
            # if guid starts with local need to remove anything after id before hashing
            if searched.tracks()[0].guid.startswith('local'):
                local_id = searched.tracks()[0].guid.split('/')[2]
                hash_str = 'local://{}'.format(local_id)
            else:
                hash_str = searched.tracks()[0].guid.replace('/1?lang=en', '?lang=en')
            # print(searched.__dict__.items())
            hash_to_path(hash_str, PLEX_LOCAL_ALBUM_PATH, searched.title, searched.type, searched.parentTitle)

        elif searched.type == 'artist':
            # If artist check over each album
            for albums in searched.albums():
                get_plex_hash(albums.title, 'album')
        else:
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Helping navigate Plex's locally stored data.")
    parser.add_argument('-s', '--search', required=True, help='Search Plex for title.')
    parser.add_argument('-m', '--media_type', help='Plex media_type to refine search for title.',
                        choices=['show', 'movie', 'episode', 'album', 'track', 'artist'])
    opts = parser.parse_args()
    if opts.media_type:
        get_plex_hash(opts.search, opts.media_type)
    else:
        get_plex_hash(opts.search)
