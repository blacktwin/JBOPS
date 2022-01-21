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

Usage:
    python merge_multiepisodes.py --library "TV Shows" --show "SpongeBob SquarePants"
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


def group_episodes(plex, library, show):
    groups = defaultdict(list)

    show = plex.library.section(library).get(show)
    for episode in show.episodes():
        groups[episode.locations[0]].append(episode)

    for index, (first, *episodes) in enumerate(groups.values()):
        if not episodes:
            continue

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

        merge(first, episodes)
        first.edit(**{
            'title.value': title[:-3],
            'title.locked': 1,
            'titleSort.value': titleSort[:-3],
            'titleSort.locked': 1,
            'summary.value': summary[:-2],
            'summary.locked': 1,
            'originallyAvailableAt.locked': 1,
            'contentRating.locked': 1,
            'index.value': index + 1,
            'index.locked': 1
        })
        first.addWriter(writers, locked=True)
        first.addDirector(directors, locked=True)


def merge(first, episodes):
    key = '%s/merge?ids=%s' % (first.key, ','.join([str(r.ratingKey) for r in episodes]))
    first._server.query(key, method=first._server._session.put)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--library', required=True)
    parser.add_argument('--show', required=True)
    opts = parser.parse_args()

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    group_episodes(plex, **vars(opts))
