#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Description: Automatically generate pinyin sort title for Chinese media library
Author: timmy0209
Maintainer: sjtuross
Requires: plexapi, pypinyin
Usage: plex-pinyin-sort.py [-h] [-u URL] [-t TOKEN] [-s SECTION]

    optional arguments:
    -h, --help            show this help message and exit
    -u URL, --url URL
    -t TOKEN, --token TOKEN
    -s SECTION, --section SECTION

Tautulli script trigger:
    * Notify on recently added

Tautulli script arguments:
    * Recently Added:
        --section {section_id}
'''

import argparse
import os
import pypinyin
from plexapi.server import PlexServer

PLEX_URL = ""
PLEX_TOKEN = ""

def check_contain_chinese(check_str):
     for ch in check_str:
         if '\u4e00' <= ch <= '\u9fff':
             return True
     return False

def changepinyin (title):
    a = pypinyin.pinyin(title, style=pypinyin.FIRST_LETTER, errors='ignore')
    b = []
    for i in range(len(a)):
        b.append(str(a[i][0]).upper())
    c = ''.join(b)
    return c

def loopThroughAllItems(plex, sectionId, regenerate):
    section=plex.library.sectionByID(int(sectionId))
    if section.type in ('movie', 'show'):
        for item in section.all():
            if check_contain_chinese(item.title if regenerate else item.titleSort):
                titleSort=changepinyin(item.title if regenerate else item.titleSort)
                item.editSortTitle(titleSort, True)
                print(section.type.capitalize(), "-", item.title)
        for collection in section.collections():
            if collection.content==None and check_contain_chinese(collection.title if regenerate else collection.titleSort):
                titleSort=changepinyin(collection.title if regenerate else collection.titleSort)
                collection.editSortTitle(titleSort, True)
                print("Collection", "-", collection.title)
    if section.type == 'artist':
        for artist in section.all():
            if check_contain_chinese(artist.title if regenerate else artist.titleSort):
                titleSort=changepinyin(artist.title if regenerate else artist.titleSort)
                artist.editSortTitle(titleSort, True)
                print(section.type.capitalize(), "-", artist.title)
            for album in artist.albums():
                if check_contain_chinese(album.title if regenerate else album.titleSort):
                    titleSort=changepinyin(album.title if regenerate else album.titleSort)
                    album.editSortTitle(titleSort, True)
                    print(section.type.capitalize(), "-", artist.title, "-", album.title)
 
    print("\nSuccess!")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url')
    parser.add_argument('-t', '--token')
    parser.add_argument('-s', '--section')
    parser.add_argument('-r', '--regenerate', nargs='?', type=int, const=1, default=0)
    opts = parser.parse_args()

    PLEX_URL = opts.url or os.getenv('PLEX_URL', PLEX_URL)
    PLEX_TOKEN = opts.token or os.getenv('PLEX_TOKEN', PLEX_TOKEN)

    if not PLEX_URL:
        PLEX_URL = input('Enter Plex Server Url:')

    if not PLEX_TOKEN:
        PLEX_TOKEN = input('Enter Plex Server Token:')

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)

    if not opts.section:
        for section in plex.library.sections():
            if section.type in ('movie', 'show', 'artist'):
                print(section)
        sectionId = input('Enter Media Library Section Id:')
    else:
        sectionId = opts.section
    
    regenerate = False if opts.regenerate==0 else True

    loopThroughAllItems(plex, sectionId, regenerate)
