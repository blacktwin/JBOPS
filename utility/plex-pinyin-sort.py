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
    a = pypinyin.pinyin(title, style=pypinyin.FIRST_LETTER)
    b = []
    for i in range(len(a)):
        b.append(str(a[i][0]).upper())
    c = ''.join(b)
    return c

def loopThroughAllItems(plex, sectionId):
    section=plex.library.sectionByID(int(sectionId))
    if section.type in ('movie', 'show', 'artist'):
        for item in section.all():
            if check_contain_chinese(item.titleSort):
                titleSort=changepinyin(item.titleSort)
                item.edit(**{"titleSort.value":titleSort, "titleSort.locked":1})
                print(item.title)
    print("Success")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url')
    parser.add_argument('-t', '--token')
    parser.add_argument('-s', '--section')
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

    loopThroughAllItems(plex, sectionId)
