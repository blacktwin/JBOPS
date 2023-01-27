#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Description:  Check media availability on streaming services.
# Author:       /u/SwiftPanda16
# Requires:     plexapi

import argparse
import os
from plexapi import CONFIG
from plexapi.server import PlexServer
from plexapi.exceptions import BadRequest

PLEX_URL = ''
PLEX_TOKEN = ''

# Environment Variables or PlexAPI Config
PLEX_URL = os.getenv('PLEX_URL', PLEX_URL) or CONFIG.data['auth'].get('server_baseurl')
PLEX_TOKEN = os.getenv('PLEX_TOKEN', PLEX_TOKEN) or CONFIG.data['auth'].get('server_token')


def check_streaming_services(plex, libraries, services, available_only):
    if libraries:
        sections = [plex.library.section(library) for library in libraries]
    else:
        sections = [
            section for section in plex.library.sections()
            if section.agent in {'tv.plex.agents.movie', 'tv.plex.agents.series'}
        ]

    for section in sections:
        print(f'{section.title}')

        for item in section.all():
            try:
                availabilities = item.streamingServices()
            except BadRequest:
                continue

            if services:
                availabilities = [
                    availability for availability in availabilities
                    if availability.title in services
                ]

            if available_only and not availabilities:
                continue

            if item.type == 'movie':
                subtitle = item.media[0].videoResolution
                subtitle = subtitle.upper() if subtitle == 'sd' else ((subtitle + 'p') if subtitle.isdigit() else '')
            else:
                subtitle = item.childCount
                subtitle = str(subtitle) + ' season' + ('s' if subtitle > 1 else '')

            print(f'  └─ {item.title} ({item.year}) ({subtitle})')

            for availability in availabilities:
                title = availability.title
                quality = availability.quality
                offerType = availability.offerType.capitalize()
                priceDescription = (' ' + availability.priceDescription) if availability.priceDescription else ''
                print(f'       └─ {title} ({quality} - {offerType}{priceDescription})')

        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--libraries',
        '-l',
        nargs='+',
        help=(
            'Plex libraries to check (e.g. Movies, TV Shows, etc.). '
            'Default: All movie and tv show libraries using the Plex Movie or Plex TV Series agents.'
        )
    )
    parser.add_argument(
        '--services',
        '-s',
        nargs='+',
        help=(
            'Streaming services to check (e.g. Netflix, Disney+, Amazon Prime Video, etc.). '
            'Note: Must be the exact name of the service as it appears in Plex. '
            'Default: All services.'
        )
    )
    parser.add_argument(
        '--available_only',
        '-a',
        action='store_true',
        help=(
            'Only list media that is available on at least one streaming service.'
        )
    )
    opts = parser.parse_args()

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    check_streaming_services(plex, **vars(opts))
