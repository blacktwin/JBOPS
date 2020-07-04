#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description: Do the Plex Dance!
Author: Blacktwin, SwiftPanda16
Requires: plexapi, requests

Original Dance moves
    1. Move all files for the media item out of the directory your Library is looking at,
        so Plex will not “see” it anymore
    2. Scan the library (to detect changes)
    3. Empty trash
    4. Clean bundles
    5. Double check naming schema and move files back
    6. Scan the library

https://forums.plex.tv/t/the-plex-dance/197064

Script Dance moves
    1. Create .plexignore file in affected items library root
        .plexignore will contain:

         # Ignoring below file for Plex Dance
         *Item_Root/*

        - if .plexignore file already exists in library root, append contents
    2. Scan the library
    3. Empty trash
    4. Clean bundles
    5. Remove or restore .plexignore
    6. Scan the library
    7. Optimize DB

 Example:
     Dance with rating key 110645
        plex_dance.py --ratingKey 110645
    
    From Unraid host OS
        plex_dance.py --ratingKey 110645 --path /mnt/user

    *Dancing only works with Show or Movie rating keys
    
 **After Dancing, if you use Tautulli the rating key of the dancing item will have changed.
    Please use this script to update your Tautulli database with the new rating key
        https://gist.github.com/JonnyWong16/f554f407832076919dc6864a78432db2
"""
from __future__ import print_function
from __future__ import unicode_literals

from plexapi.server import PlexServer
from plexapi.server import CONFIG
import requests
import argparse
import time
import os

# Using CONFIG file
PLEX_URL = ''
PLEX_TOKEN = ''

IGNORE_FILE = "# Ignoring below file for Plex Dance\n{}"

if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token')
if not PLEX_URL:
    PLEX_URL = CONFIG.data['auth'].get('server_baseurl')

session = requests.Session()
# Ignore verifying the SSL certificate
session.verify = False  # '/path/to/certfile'
# If verify is set to a path to a directory,
# the directory must have been processed using the c_rehash utility supplied
# with OpenSSL.
if session.verify is False:
    # Disable the warning that the request is insecure, we know that...
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=session)


def section_path(section, filepath):
    for location in section.locations:
        if filepath.startswith(location):
            return location


def refresh_section(sectionID):
    plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=session)
    section = plex.library.sectionByID(sectionID)
    section.update()
    time.sleep(10)
    plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=session)
    section = plex.library.sectionByID(sectionID)
    while section.refreshing is True:
        time.sleep(10)
        print("Waiting for library to finish refreshing to continue dance.")
        plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=session)
        section = plex.library.sectionByID(sectionID)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Do the Plex Dance!",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--ratingKey', nargs="?", type=int, required=True,
                        help='Rating key of item that needs to dance.')
    parser.add_argument('--path', nargs="?", type=str,
                        help='Prefix path for libraries behind mount points.\n'
                             'Example: /mnt/user Resolves: /mnt/user/library_root')

    opts = parser.parse_args()

    item = plex.fetchItem(opts.ratingKey)
    item.reload()
    sectionID = item.librarySectionID
    section = plex.library.sectionByID(sectionID)
    old_plexignore = ''

    if item.type == 'movie':
        item_file = item.media[0].parts[0].file
        locations = os.path.split(item.locations[0])
        item_root = os.path.split(locations[0])[1]
        library_root = section_path(section, locations[0])
    elif item.type == 'show':
        locations = os.path.split(item.locations[0])
        item_root = locations[1]
        library_root = section_path(section, locations[0])
    else:
        print("Media type not supported.")
        exit()

    library_root = opts.path + library_root if opts.path else library_root
    plexignore = IGNORE_FILE.format('*' + item_root + '/*')
    item_ignore = os.path.join(library_root, '.plexignore')
    # Check for existing .plexignore file in library root
    if os.path.exists(item_ignore):
        # If file exists append new ignore params and store old params
        with open(item_ignore, 'a+') as old_file:
            old_plexignore = old_file.readlines()
            old_file.write('\n' + plexignore)

    # 1. Create .plexignore file
    print("Creating .plexignore file for dancing.")
    with open(item_ignore, 'w') as f:
        f.write(plexignore)
    # 2. Scan library
    print("Refreshing library of dancing item.")
    refresh_section(sectionID)
    # 3. Empty library trash
    print("Emptying Trash from library.")
    section.emptyTrash()
    time.sleep(5)
    # 4. Clean library bundles
    print("Cleaning Bundles from library.")
    plex.library.cleanBundles()
    time.sleep(5)
    # 5. Remove or restore .plexignore
    if old_plexignore:
        print("Replacing new .plexignore with old .plexignore.")
        with open(item_ignore, 'w') as new_file:
            new_file.writelines(old_plexignore)
    else:
        print("Removing .plexignore file from dancing directory.")
        os.remove(item_ignore)
    # 6. Scan library
    print("Refreshing library of dancing item.")
    refresh_section(sectionID)
    # 7. Optimize DB
    print("Optimizing library database.")
    plex.library.optimize()
