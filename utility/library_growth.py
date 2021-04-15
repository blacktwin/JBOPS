#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Check Plex library locations growth over time using added date.
Check Plex, Tautulli, OS for added time, last updated, originally availableAt, played dates
"""

import argparse
import datetime
import sys
from plexapi.server import PlexServer
from plexapi.server import CONFIG
import requests
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
from collections import Counter
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})

PLEX_URL =''
PLEX_TOKEN = ''
TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''

# Using CONFIG file
if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token')
if not PLEX_URL:
    PLEX_URL = CONFIG.data['auth'].get('server_baseurl')
if not TAUTULLI_URL:
    TAUTULLI_URL = CONFIG.data['auth'].get('tautulli_baseurl')
if not TAUTULLI_APIKEY:
    TAUTULLI_APIKEY = CONFIG.data['auth'].get('tautulli_apikey')

VERIFY_SSL = False

sess = requests.Session()
sess.verify = False


plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)
sections = [x for x in plex.library.sections() if x.type not in ['artist', 'photo']]
sections_dict = {x.key: x.title for x in sections}


def graph_setup():
    fig, axs = plt.subplots(3)
    fig.set_size_inches(14, 12)
    
    return axs


def exclusions(all_true, select, all_items):
    """
    Parameters
    ----------
    all_true: bool
        All of something (allLibraries, allPlaylists, allUsers)
    select: list
        List from arguments (user, playlists, libraries)
    all_items: list or dict
        List or Dictionary of all possible somethings

    Returns
    -------
    output: list or dict
        List of what was included/excluded
    """
    output = ''
    if isinstance(all_items, list):
        output = []
        if all_true and not select:
            output = all_items
        elif not all_true and select:
            for item in all_items:
                if isinstance(item, str):
                    return select
                else:
                    if item.title in select:
                        output.append(item)
        elif all_true and select:
            for x in select:
                all_items.remove(x)
                output = all_items

    elif isinstance(all_items, dict):
        output = {}
        if all_true and not select:
            output = all_items
        elif not all_true and select:
            for key, value in all_items.items():
                if value in select:
                    output[key] = value
        elif all_true and select:
            for key, value in all_items.items():
                if value not in select:
                    output[key] = value

    return output


def plex_growth(section, axs):
    library = plex.library.sectionByID(section)

    allthem = library.all()
    
    allAddedAt = [x.addedAt.date() for x in allthem if x.addedAt]
    y = range(len(allAddedAt))
    axs[0].plot(sorted(allAddedAt), y)
    axs[0].set_title('Plex {} Library Growth'.format(library.title))


def plex_released(section, axs):
    
    library = plex.library.sectionByID(section)
    allthem = library.all()
    
    originallyAvailableAt = [x.originallyAvailableAt.date().strftime('%Y')
                             for x in allthem if x.originallyAvailableAt]
    counts = Counter(sorted(originallyAvailableAt))

    axs[1].bar(list(counts.keys()), list(counts.values()))
    loc = plticker.MultipleLocator(base=5.0) # this locator puts ticks at regular intervals
    axs[1].xaxis.set_major_locator(loc)
    axs[1].set_title('Plex {} Library Released Date'.format(library.title))
    
    releasedGenres = {}
    genres = []
    for x in allthem:
        if x.originallyAvailableAt:
            releaseYear = x.originallyAvailableAt.date().strftime('%Y')
            if releasedGenres.get(releaseYear):
                for genre in x.genres:
                    releasedGenres[releaseYear].append(genre.tag)
                    genres.append(genre.tag)
            else:
                for genre in x.genres:
                    releasedGenres[releaseYear] = [genre.tag]
                    genres.append(genre.tag)

    labels = sorted(list(set(genres)))
    for year, genre in sorted(releasedGenres.items()):
        yearGenre = Counter(sorted(genre))
        genresCounts = list(yearGenre.values())
        for i in range(len(yearGenre)):
            axs[2].bar(year, genresCounts, bottom=sum(genresCounts[:i]))
        
        loc = plticker.MultipleLocator(base=5.0) # this locator puts ticks at regular intervals
        axs[2].xaxis.set_major_locator(loc)
    axs[2].legend(labels, bbox_to_anchor=(0, -0.25, 1., .102), loc='lower center',
       ncol=12, mode="expand", borderaxespad=0.)
    axs[2].set_title('Plex {} Library Released Date (Genre)'.format(library.title))
    # plt.tight_layout()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Show library growth.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--libraries', nargs='+', choices=sections_dict.values(), metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are:\n'
                             'Choices: %(choices)s')
    parser.add_argument('--allLibraries', default=False, action='store_true',
                        help='Select all libraries.')
    
    opts = parser.parse_args()
    # Defining libraries
    libraries = exclusions(opts.allLibraries, opts.libraries, sections_dict)
    
    for library in libraries:
        library_title = sections_dict.get(library)
        print("Starting {}".format(library_title))
        graph = graph_setup()
        plex_growth(library, graph)
        plex_released(library, graph)
        plt.savefig('{}_library_growth.png'.format(library_title), bbox_inches='tight', dpi=100)
        # plt.show()