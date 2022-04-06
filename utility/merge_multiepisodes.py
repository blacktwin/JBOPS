#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Description:  Automatically merge multi-episode files in Plex into a single entry.
Author:       /u/SwiftPanda16
Requires:     plexapi
Notes:
    * All episodes **MUST** be organized correctly according to Plex's "Multiple Episodes in a Single File".
        https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/#toc-4

    * Episode titles, summaries, and tags will be appended to the first episode of the group.

    * Without re-numbering will keep the episode number of the first episode of each group.

    * Re-numbering starts at the first group episode's number and increments by one. Skipping numbers is not supported.
        * e.g. s01e01-e02, s01e03, s01e04, s01e05-e06 --> s01e01, s01e02, s01e03, s01e04
        * e.g. s02e05-e06, s01e07-e08, s02e09-e10 --> s02e05, s02e06, s02e07
        * e.g. s03e01-e02, s03e04, s03e07-e08 --> s03e01, s03e02, s03e03 (s03e03, s03e05, so3e06 skipped)

    * To revert the changes and split the episodes again, the show must be removed and re-added to Plex (aka Plex Dance).

Usage:
    * Without renumbering episodes:
        python merge_multiepisodes.py --library "TV Shows" --show "SpongeBob SquarePants"

    * With renumbering episodes:
        python merge_multiepisodes.py --library "TV Shows" --show "SpongeBob SquarePants" --renumber
'''

import argparse
import os
from collections import defaultdict
from plexapi.server import PlexServer


# ## EDIT SETTINGS ##

PLEX_URL = ''
PLEX_TOKEN = ''

# Environmental Variables
PLEX_URL = os.getenv('PLEX_URL', PLEX_URL)
PLEX_TOKEN = os.getenv('PLEX_TOKEN', PLEX_TOKEN)


def group_episodes(plex, library, show, renumber):
    show = plex.library.section(library).get(show)

    for season in show.seasons():
        groups = defaultdict(list)
        startIndex = None

        for episode in season.episodes():
            groups[episode.locations[0]].append(episode)
            if startIndex is None:
                startIndex = episode.index

        for index, (first, *episodes) in enumerate(groups.values(), start=startIndex):
            title = first.title + ' / '
            titleSort = first.titleSort + ' / '
            summary = first.summary + '\n\n'
            writers = []
            directors = []

            for episode in episodes:
                title += episode.title + ' / '
                titleSort += episode.titleSort + ' / '
                summary += episode.summary + '\n\n'
                writers.extend([writer.tag for writer in episode.writers])
                directors.extend([director.tag for director in episode.directors])

            if episodes:
                merge(first, episodes)

            first.addWriter(writers, locked=True)
            first.addDirector(directors, locked=True)

            edits = {
                'title.value': title[:-3],
                'title.locked': 1,
                'titleSort.value': titleSort[:-3],
                'titleSort.locked': 1,
                'summary.value': summary[:-2],
                'summary.locked': 1,
                'originallyAvailableAt.locked': 1,
                'contentRating.locked': 1
            }

            if renumber:
                edits['index.value'] = index
                edits['index.locked'] = 1

            first.edit(**edits)


def merge(first, episodes):
    key = '%s/merge?ids=%s' % (first.key, ','.join([str(r.ratingKey) for r in episodes]))
    first._server.query(key, method=first._server._session.put)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--library', required=True)
    parser.add_argument('--show', required=True)
    parser.add_argument('--renumber', action='store_true')
    opts = parser.parse_args()

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    group_episodes(plex, **vars(opts))
