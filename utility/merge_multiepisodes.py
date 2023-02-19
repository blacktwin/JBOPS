#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Description:  Automatically merge multi-episode files in Plex into a single entry.
Author:       /u/SwiftPanda16
Requires:     plexapi, pillow (optional)
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

    * With renumbering episodes and composite thumb:
        python merge_multiepisodes.py --library "TV Shows" --show "SpongeBob SquarePants" --renumber --composite-thumb
'''

import argparse
import functools
import io
import math
import os
import requests
from collections import defaultdict
from plexapi.server import PlexServer

try:
    from PIL import Image, ImageDraw
    hasPIL = True
except ImportError:
    hasPIL = False


# ## EDIT SETTINGS ##

PLEX_URL = ''
PLEX_TOKEN = ''

# Composite Thumb Settings
WIDTH, HEIGHT = 640, 360  # 16:9 aspect ratio
LINE_ANGLE = 25  # degrees
LINE_THICKNESS = 10


# Environmental Variables
PLEX_URL = os.getenv('PLEX_URL', PLEX_URL)
PLEX_TOKEN = os.getenv('PLEX_TOKEN', PLEX_TOKEN)


def group_episodes(plex, library, show, renumber, composite_thumb):
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
                if composite_thumb:
                    firstImgFile = download_image(
                        plex.transcodeImage(first.thumbUrl, width=WIDTH, height=HEIGHT)
                    )
                    lastImgFile = download_image(
                        plex.transcodeImage(episodes[-1].thumbUrl, width=WIDTH, height=HEIGHT)
                    )
                    compImgFile = create_composite_thumb(firstImgFile, lastImgFile)
                    first.uploadPoster(filepath=compImgFile)

                merge(first, episodes)

            first.batchEdits() \
                .editTitle(title[:-3]) \
                .editSortTitle(titleSort[:-3]) \
                .editSummary(summary[:-2]) \
                .editContentRating(first.contentRating) \
                .editOriginallyAvailable(first.originallyAvailableAt) \
                .addWriter(writers) \
                .addDirector(directors) \

            if renumber:
                first._edits['index.value'] = index
                first._edits['index.locked'] = 1

            first.saveEdits()


def merge(first, episodes):
    key = '%s/merge?ids=%s' % (first.key, ','.join([str(r.ratingKey) for r in episodes]))
    first._server.query(key, method=first._server._session.put)


def download_image(url):
    r = requests.get(url, stream=True)
    r.raw.decode_content = True
    return r.raw


def create_composite_thumb(firstImgFile, lastImgFile):
    mask, line = create_masks()

    # Open and crop first image
    firstImg = Image.open(firstImgFile)
    width, height = firstImg.size
    firstImg = firstImg.crop(
        (
            (width - WIDTH) // 2,
            (height - HEIGHT) // 2,
            (width + WIDTH) // 2,
            (height + HEIGHT) // 2
        )
    )

    # Open and crop last image
    lastImg = Image.open(lastImgFile)
    width, height = lastImg.size
    lastImg = lastImg.crop(
        (
            (width - WIDTH) // 2,
            (height - HEIGHT) // 2,
            (width + WIDTH) // 2,
            (height + HEIGHT) // 2
        )
    )

    # Create composite image
    comp = Image.composite(line, Image.composite(firstImg, lastImg, mask), line)

    # Return composite image as file-like object
    compImgFile = io.BytesIO()
    comp.save(compImgFile, format='jpeg')
    compImgFile.seek(0)
    return compImgFile


@functools.lru_cache(maxsize=None)
def create_masks():
    scale = 3  # For line anti-aliasing
    offset = HEIGHT // 2 * math.tan(LINE_ANGLE * math.pi / 180)

    # Create diagonal mask
    mask = Image.new('L', (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(
        (
            (0, 0),
            (WIDTH // 2 + offset, 0),
            (WIDTH // 2 - offset, HEIGHT),
            (0, HEIGHT)
        ),
        fill=255
    )

    # Create diagonal line (use larger image then scale down with anti-aliasing)
    line = Image.new('L', (scale * WIDTH, scale * HEIGHT), 0)
    draw = ImageDraw.Draw(line)
    draw.line(
        (
            (scale * (WIDTH // 2 + offset), -scale),
            (scale * (WIDTH // 2 - offset), scale * (HEIGHT + 1))
        ),
        fill=255,
        width=scale * LINE_THICKNESS
    )
    line = line.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    return mask, line


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--library', required=True)
    parser.add_argument('--show', required=True)
    parser.add_argument('--renumber', action='store_true')
    parser.add_argument('--composite_thumb', action='store_true')
    opts = parser.parse_args()

    if opts.composite_thumb and not hasPIL:
        print('PIL is not installed. Please install `pillow` to create composite thumbnails.')
        exit(1)

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    group_episodes(plex, **vars(opts))
