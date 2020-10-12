#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pull poster images from Imgur and places them inside Shows root folder.
    /path/to/show/Show.jpg

Skips download if showname.jpg exists or if show does not exist.

"""
from __future__ import print_function
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import object
import requests
import urllib.request, urllib.parse, urllib.error
import os


# ## Edit ##

# Imgur info
CLIENT_ID = 'xxxxx'  # Tautulli Settings > Notifications > Imgur Client ID
ALBUM_ID = '7JeSw'  # http://imgur.com/a/7JeSw  <--- 7JeSw is the ablum_id

# Local info
SHOW_PATH = 'D:\\Shows\\'

# ## /Edit ##


class IMGURINFO(object):
    def __init__(self, data=None):
        d = data or {}
        self.link = d['link']
        self.description = d['description']


def get_imgur():
    url = "https://api.imgur.com/3/album/{ALBUM_ID}/images".format(ALBUM_ID=ALBUM_ID)
    headers = {'authorization': 'Client-ID {}'.format(CLIENT_ID)}
    r = requests.get(url, headers=headers)
    imgur_dump = r.json()
    return[IMGURINFO(data=d) for d in imgur_dump['data']]


for x in get_imgur():
    # Check if Show directory exists
    if os.path.exists(os.path.join(SHOW_PATH, x.description)):
        # Check if Show poster (show.jpg) exists
        if os.path.exists((os.path.join(SHOW_PATH, x.description, x.description))):
            print("Poster for {} was already downloaded or filename already exists, skipping.".format(x.description))
        else:
            print("Downloading poster for {}.".format(x.description))
            urllib.request.urlretrieve(x.link, '{}.jpg'.format((os.path.join(SHOW_PATH, x.description, x.description))))
    else:
        print("{} - {} did not match your library.".format(x.description, x.link))
