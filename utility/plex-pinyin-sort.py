#!/usr/bin/env python

'''
Description: Automatically generate pinyin sort title for Chinese movie library
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

import urllib
import http.client
import json
import argparse
import os
import xmltodict
import pypinyin
from plexapi.server import PlexServer

PLEX_URL = ""
PLEX_TOKEN = ""

def fetchPlexApi(path='', method='GET', getFormPlextv=False, token=PLEX_TOKEN, params=None):
        """a helper function that fetches data from and put data to the plex server"""
        #print(path)
        headers = {'X-Plex-Token': token,
                'Accept': 'application/json'}
        if getFormPlextv:
            url = 'plex.tv'        
            connection = http.client.HTTPSConnection(url)
        else:
            url = PLEX_URL.rstrip('/').replace('http://','')     
            connection = http.client.HTTPConnection(url)
        try:
            if method.upper() == 'GET':
                pass
            elif method.upper() == 'POST':
                headers.update({'Content-type': 'application/x-www-form-urlencoded'})
                pass
            elif method.upper() == 'PUT':
                pass
            elif method.upper() == 'DELETE':
                pass
            else:
                print("Invalid request method provided: {method}".format(method=method))
                connection.close()
                return

            connection.request(method.upper(), path , params, headers)     
            response = connection.getresponse()         
            r = response.read()             
            contentType = response.getheader('Content-Type')      
            status = response.status    
            connection.close()

            if response and len(r):     
                if 'application/json' in contentType:         
                    return json.loads(r)
                elif 'application/xml' in contentType:
                    return xmltodict.parse(r)
                else:
                    return r
            else:
                return r

        except Exception as e:
            connection.close()
            print("Error fetching from Plex API: {err}".format(err=e))

def updateSortTitle(rating,item):
    sortQuery =urllib.parse.quote(item.encode('utf-8'))                                
    data = fetchPlexApi("/library/sections/"+sectionNum+"/all?type=1&id=%s&titleSort.value=%s&"%(rating,sortQuery), "PUT",token=PLEX_TOKEN) 

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

def loopThroughAllMovies():
    toDo = True
    start = 0
    size = 100
    while toDo:
        if len(sectionNum):
            url = "/library/sections/" + sectionNum + "/all?type=1&X-Plex-Container-Start=%i&X-Plex-Container-Size=%i" % (start, size)
            metadata = fetchPlexApi(url,token=PLEX_TOKEN)
            container = metadata["MediaContainer"]
            elements = container["Metadata"]
            totalSize = container["totalSize"]
            offset = container["offset"]
            size = container["size"]      
            start = start + size        
            if totalSize-offset-size == 0:
                toDo = False
            # loop through all elements
            for movie in elements:
                mediaType = movie["type"]
                if mediaType != "movie":
                    continue
                if 'titleSort' in movie:
                    titleSort = movie["titleSort"]
                    if not check_contain_chinese(titleSort):
                        continue
                title = movie["title"]
                if check_contain_chinese(title):
                    titleSort = changepinyin(title)
                    print(title)
                    key = movie["ratingKey"]        
                    updateSortTitle(key, titleSort)
    print("Success!")

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
            if section.type == 'movie':
                print(section)
        sectionNum = input('Enter Movie Library Section Id:')
    else:
        sectionNum = opts.section

    loopThroughAllMovies()
