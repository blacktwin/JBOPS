#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Description:  Removes ALL collections from ALL movies.
# Author:       /u/SwiftPanda16
# Requires:     plexapi

from __future__ import unicode_literals
from plexapi.server import PlexServer

### EDIT SETTINGS ###

PLEX_URL = "http://localhost:32400"
PLEX_TOKEN = "xxxxxxxxxx"
MOVIE_LIBRARY_NAME = "Movies"


## CODE BELOW ##

plex = PlexServer(PLEX_URL, PLEX_TOKEN)

for movie in plex.library.section(MOVIE_LIBRARY_NAME).all():
    movie.removeCollection([c.tag for c in movie.collections])
