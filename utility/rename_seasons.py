#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Description:  Rename season title for TV shows on Plex.
# Author:       /u/SwiftPanda16
# Requires:     plexapi

from __future__ import print_function
from __future__ import unicode_literals
from plexapi.server import PlexServer


### EDIT SETTINGS ###

PLEX_URL = "http://localhost:32400"
PLEX_TOKEN = "xxxxxxxxxx"

TV_SHOW_LIBRARY = "TV Shows"
TV_SHOW_NAME = "Sailor Moon"
SEASON_MAPPINGS = {
    "Season 1": "Sailor Moon",               # Season 1 will be renamed to Sailor Moon
    "Season 2": "Sailor Moon R",             # Season 2 will be renamed to Sailor Moon R
    "Season 3": "Sailor Moon S",             # etc.
    "Season 4": "Sailor Moon SuperS",
    "Season 5": "Sailor Moon Sailor Stars",
    "Bad Season Title": "",                  # Blank string "" to reset season title
}


## CODE BELOW ##

def main():
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    
    show = plex.library.section(TV_SHOW_LIBRARY).get(TV_SHOW_NAME)
    print("Found TV show '{}' in the '{}' library on Plex.".format(TV_SHOW_NAME, TV_SHOW_LIBRARY))
        
    for season in show.seasons():
        old_season_title = season.title
        new_season_title = SEASON_MAPPINGS.get(season.title)
        if new_season_title:
            season.edit(**{"title.value": new_season_title, "title.locked": 1})
            print("'{}' renamed to '{}'.".format(old_season_title, new_season_title))
        elif new_season_title == "":
            season.edit(**{"title.value": new_season_title, "title.locked": 0})
            print("'{}' reset to '{}'.".format(old_season_title, season.reload().title))
        else:
            print("No mapping for '{}'. Season not renamed.".format(old_season_title))


if __name__ == "__main__":
    main()

    print("Done.")
