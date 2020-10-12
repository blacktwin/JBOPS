#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Delete all playlists from Plex.


"""
from __future__ import unicode_literals

from plexapi.server import PlexServer

baseurl = 'http://localhost:32400'
token = 'XXXXXXXX'
plex = PlexServer(baseurl, token)


for playlist in plex.playlists():
    playlist.delete()
