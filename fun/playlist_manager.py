#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description: Create and share playlists based on Most Popular TV/Movies from Tautulli
                and Aired this day in history.
Author: blacktwin
Requires: requests, plexapi

Create, share, and clean Playlists for users.

optional arguments:
  -h, --help            show this help message and exit
  --jbop                Playlist selector.
                        Choices: (historyToday, historyWeek, historyMonth, popularTv, popularMovies)
  --action              Action selector.
                        add - create new playlist for admin or users
                        remove - remove playlist type or name from admin or users
                        update - remove playlist type and create new playlist type for admin or users
                        show - show contents of playlist type or admin or users current playlists
                        share - share existing playlist by title from admin to users

  --users {]            The Plex usernames to create/share to or delete from.
                        Choices:  (USERNAMES)
  --libraries  [ ...]   Space separated list of case sensitive names to
                        process. Allowed names are:
                        Choices: (LIBRARIES)
  --allLibraries        Select all libraries.
  --self                Create playlist for admin.
                        Default: False
  --days DAYS           The time range to calculate statistics.
                        Default: 30
  --top TOP             The number of top items to list.
                        Default: 5
  --playlists           Space separated list of case sensitive names to
                        process. Allowed names are:
                        Choices: (PLAYLISTS)
  --allPlaylist         Select all playlists.
  --name NAME           Custom name for playlist.
  --limit LIMIT         Limit the amount items to be added to a playlist.
  --filter FILTER       Search filtered metadata fields
                        Filters: (mood unwatched country contentRating collection label director duplicate
                        studio actor year genre guid resolution decade network).
  --search SEARCH       Search non-filtered metadata fields for keywords in title, summary, etc.


 Example:
    Use with cron or task to schedule runs

 Create Aired Today Playlist from Movies and TV Shows libraries for admin user
    python playlist_manager.py --jbop historyToday --libraries Movies "TV Shows" --action add

 Create Aired Today Playlist from Movies and TV Shows libraries and share to users bob, Black Twin and admin user
    python playlist_manager.py --jbop historyToday --libraries Movies "TV Shows" --action add --users bob "Black Twin" --self

 Update previous Aired Today Playlist(s) from Movies and TV Shows libraries and share to users bob and Black Twin
    python playlist_manager.py --jbop historyToday --libraries Movies "TV Shows" --action update --users bob "Black Twin"

 Delete all previous Aired Today Playlist(s) from users bob and Black Twin
    python playlist_manager.py --jbop historyToday --action remove --users bob "Black Twin"

 Create 5 Most Popular TV Shows (30 days) Playlist and share to users bob and Black Twin
    python playlist_manager.py --jbop popularTv --action add --users bob "Black Twin"

 Create 10 Most Popular Movies (60 days) Playlist and share to users bob and Black Twin
    python playlist_manager.py --jbop popularMovies --action add --users bob "Black Twin" --days 60 --top 10

 Show 5 Most Popular TV Shows (30 days) Playlist
    python playlist_manager.py --jbop popularTv --action show

 Show all users current playlists
    python playlist_manager.py --action show --allUsers

 Share existing admin Playlists "My Custom Playlist" and "Another Playlist" with all users
    python playlist_manager.py --action share --allUsers --playlists "My Custom Playlist" "Another Playlist"

 Search and Filter;

 metadata_field_name = title, summary, etc.

 --search {metadata_field_name}=value
    search through metadata field for existence of value.

 --search {metadata_field_name}=value1,value2,*
    search through metadata field for existence of values.
        *comma separated for AND (value1 AND value2 AND *)



 Excluding;

 --user becomes excluded if --allUsers is set
   python playlist_manager.py --action show --allUsers --user USER
       - Show all users current Playlists... all users but USER

 --libraries becomes excluded if --allLibraries is set
   python playlist_manager.py --jbop historyToday --allLibraries --libraries Movies --action add
       - Create Aired Today Playlist from every library by Movies for admin user

"""

import sys
import os
import random
import logging
import requests
import argparse
import operator
import datetime
import unicodedata
from collections import Counter
from plexapi.server import PlexServer, CONFIG

filename = os.path.basename(__file__)
filename = filename.split('.')[0]

logger = logging.getLogger(filename)
logger.setLevel(logging.DEBUG)

error_format = logging.Formatter('%(asctime)s:%(name)s:%(funcName)s:%(message)s')
stream_format = logging.Formatter('%(message)s')

file_handler = logging.FileHandler('{}.log'.format(filename))
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(error_format)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(stream_format)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


# ### EDIT SETTINGS ###

PLEX_URL = ''
PLEX_TOKEN = ''
TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''

# ## CODE BELOW ##

if not PLEX_URL:
    PLEX_URL = CONFIG.data['auth'].get('server_baseurl')
if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token')
if not TAUTULLI_URL:
    TAUTULLI_URL = CONFIG.data['auth'].get('tautulli_baseurl')
if not TAUTULLI_APIKEY:
    TAUTULLI_APIKEY = CONFIG.data['auth'].get('tautulli_apikey')

# Defaults
DAYS = 30
TOP = 5

sess = requests.Session()
# Ignore verifying the SSL certificate
sess.verify = False  # '/path/to/certfile'
# If verify is set to a path to a directory,
# the directory must have been processed using the c_rehash utility supplied
# with OpenSSL.
if sess.verify is False:
    # Disable the warning that the request is insecure, we know that...
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)
account = plex.myPlexAccount()

user_lst = [x.title for x in plex.myPlexAccount().users() if x.servers and x.friend]
sections = plex.library.sections()
sections_dict = {x.key: x.title for x in sections}
filters_lst = list(set([y for x in sections if x.type != 'photo' for y in x.ALLOWED_FILTERS]))
playlist_lst = [x.title for x in plex.playlists()]
today = datetime.datetime.now().date()
weeknum = datetime.date(today.year, today.month, today.day).isocalendar()[1]


def actions():
    """
    add - create new playlist for admin or users
    remove - remove playlist type or name from admin or users
    update - remove playlist type and create new playlist type for admin or users
    show - show contents of playlist type or admin or users current playlists
    share - share existing playlist by title from admin to users
    """
    return ['add', 'remove', 'update', 'show', 'share']


def selectors():
    """Predefined Playlist selections and titles
    """
    selections = {'historyToday': 'Aired Today {month}-{day} in History',
                  'historyWeek': 'Aired This Week ({week}) in History',
                  'historyMonth': 'Aired in {month}',
                  'popularTv': 'Most Popular TV Shows ({days} days)',
                  'popularMovies': 'Most Popular Movies ({days} days)',
                  'custom': '{custom} Playlist',
                  'random': '{count} Random {libraries} Playlist'
                  }

    return selections


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
            output = select
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


def get_home_stats(time_range, stats_count):
    # Get the homepage watch statistics.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_home_stats',
               'time_range': time_range,
               'stats_count': stats_count,
               'stats_type': 0}  # stats_type = plays

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']
        return res_data

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_home_stats' request failed: {0}.".format(e))


def sort_by_dates(video, date_type):
    """Find air dates of content

    Parameters
    ----------
    video
        video object to find air date

    Returns
    -------
    list
        list of rating key and date aired
    """

    try:
        ad_year = video.originallyAvailableAt.year
        ad_month = video.originallyAvailableAt.month
        ad_day = video.originallyAvailableAt.day
        ad_week = int(datetime.date(ad_year, ad_month, ad_day).isocalendar()[1])

        if date_type == 'historyToday':
            if ad_month == today.month and ad_day == today.day:
                return [[video.ratingKey] + [str(video.originallyAvailableAt)]]
        elif date_type == 'historyWeek':
            if ad_week == weeknum:
                return [[video.ratingKey] + [str(video.originallyAvailableAt)]]
        elif date_type == 'historyMonth':
            if ad_month == today.month:
                return [[video.ratingKey] + [str(video.originallyAvailableAt)]]
        else:
            logger.debug("{} is outside of range for {}".format(video.title, date_type))
            pass
    # todo-me return object
    except Exception as e:
        logger.error("Error:{} for {}".format(e, video._prettyfilename()))
        # exit()


def multi_filter_search(keyword_dict, library, search_eps=None):
    """Allowing for multiple filter or search values

    Parameters
    ----------
    keyword_dict: dict
    library: class
    search_eps: bool

    Returns
    -------
    list
        items that include all searched or filtered values
    """
    multi_lst = []
    ep_lst = []
    logs = {}
    ep_logs = []
    # How many keywords
    keyword_count = len(keyword_dict)
    for key, values in keyword_dict.items():
        if isinstance(values, list):
            keyword_count += 1
            for value in values:
                search_dict = {}
                search_dict[key] = value
                if search_eps:
                    logs["data"] = [{key: value}]
                    for show in library.all():
                        for episode in show.episodes(**search_dict):
                            ep_lst += [episode.ratingKey]
                            ep_logs += [episode.title, episode.summary]

                        logs["data"].append({"keys": ep_lst, "info": ep_logs})
                    search_lst = ep_lst
                else:
                    search_lst = [item.ratingKey for item in library.all(**search_dict)]
                multi_lst += search_lst
        else:
            if search_eps:
                for show in library.all():
                    for episode in show.episodes(**{key: values}):
                        ep_lst += [episode.ratingKey]
                multi_lst += ep_lst

            else:
                multi_lst += [item.ratingKey for item in library.all(**{key: values})]
    counts = Counter(multi_lst)
    # Use amount of keywords to check that all keywords were found in results
    search_lst = [id for id in multi_lst if counts[id] >= keyword_count]

    return list(set(search_lst))


def get_content(libraries, jbop, filters=None, search=None, limit=None):
    """Get all movies or episodes from LIBRARY_NAME.

    Parameters
    ----------
    libraries: dict
        dict of libraries key and name
    jbop: str
        jbop value for searching

    Returns
    -------
    list
        Sorted list of Movie and episodes that
        aired on today's date.

    """
    child_lst = []
    filter_lst = []
    search_lst = []
    keywords = {}
    tags = "__tag__icontains"

    if search or filters:
        if search:
            # todo-me replace with documentation showing the available search operators
            keywords = {key + '__icontains': value for key, value in search.items()}
        # Loop through each library
        for library in libraries.keys():
            plex_library = plex.library.sectionByID(library)
            library_type = plex_library.type
            # Find media type, if show then search/filter episodes
            if library_type == 'movie':
                # Decisions to stack filter and search
                if keywords:
                    child_lst += multi_filter_search(keywords, plex_library)
                if filters:
                    # Update filters for tagged filtered keys
                    for key, value in filters.items():
                        # Genre needs special handling
                        if key == "genre":
                            del filters[key]
                            filters[key + tags] = value
                    for key, value in filters.items():
                        # Only genre filtering should allow multiple values and allow for AND statement
                        if key.endswith(tags):
                            child_lst += multi_filter_search({key: value}, plex_library)
                        else:
                            filter_lst = [movie.ratingKey for movie in plex_library.search(**{key: value})]
                            child_lst += filter_lst
                if keywords and filters:
                    child_lst += list(set(filter_lst) & set(search_lst))

            elif library_type == 'show':
                # Decisions to stack filter and search
                if keywords:
                    search_lst = multi_filter_search(keywords, plex_library, search_eps=True)
                    child_lst += search_lst
                if filters:
                    # Update filters for tagged filtered keys
                    for key, value in filters.items():
                        # Genre needs special handling
                        if key == "genre":
                            del filters[key]
                            filters[key + tags] = value
                    for key, value in filters.items():
                        # Only genre filtering should allow multiple values and allow for AND statement
                        if key.endswith(tags):
                            shows_lst = multi_filter_search({key: value}, plex_library)
                        else:
                            shows_lst = [show.ratingKey for show in plex_library.search(**{key: value})]
                        for showkey in shows_lst:
                            show = plex.fetchItem(showkey)
                            for episode in show.episodes():
                                filter_lst += [episode.ratingKey]
                        child_lst += filter_lst

                if keywords and filters:
                    child_lst += list(set(filter_lst) & set(search_lst))
            else:
                pass
        # Keep only results found from both search and filters
        if keywords and filters:
            child_lst = list(set(i for i in child_lst if child_lst.count(i) > 1))

        play_lst = child_lst

    else:
        for library_id in libraries.keys():
            plex_library = plex.library.sectionByID(library_id)
            library_type = plex_library.type
            if library_type == 'movie':
                for child in plex_library.all():
                    if jbop.startswith("history"):
                        if sort_by_dates(child, jbop):
                            item_date = sort_by_dates(child, jbop)
                            child_lst += item_date
                    else:
                        child_lst += [child.ratingKey]
            elif library_type == 'show':
                for child in plex_library.all():
                    for episode in child.episodes():
                        if jbop.startswith("history"):
                            if sort_by_dates(episode, jbop):
                                item_date = sort_by_dates(episode, jbop)
                                child_lst += item_date
                        else:
                            child_lst += [episode.ratingKey]
            else:
                 pass
        # check if sort_by_dates was used
        if isinstance(child_lst[0], list):
            # Sort by original air date, oldest first
            # todo-me move sorting and add more sorting options
            aired_lst = sorted(child_lst, key=operator.itemgetter(1))

            # Remove date used for sorting
            play_lst = [x[0] for x in aired_lst]
        else:
            # todo-me probably will want to check limit by itself
            if jbop == "random" and limit:
                child_lst = random.sample(child_lst, limit)
            play_lst = child_lst

    return play_lst


def build_playlist(jbop, libraries=None, days=None, top=None, filters=None, search=None, limit=None):
    """
    Parameters
    ----------
    jbop: str
        The predefined Playlist type
    libraries: dict
        {key: name}
        Libraries to use to build Playlist
    days: int
        Days to search for Top Movies/Tv Shows
    top: int
        Limit to search for Top Movies/Tv Shows

    Returns
    -------
    key_list

    """
    keys_list = []
    if jbop in ['popularTv', 'popularMovies']:
        home_stats = get_home_stats(days, top)
        for stat in home_stats:
            if stat['stat_id'] in ['popular_tv', 'popular_movies']:
                keys_list += [x['rating_key'] for x in stat['rows'] if
                              str(x['section_id']) in libraries.keys()]
    else:
        try:
            keys_list = get_content(libraries, jbop, filters, search, limit)
        except TypeError as e:
            logger.exception("Libraries are not defined for {}. Use --libraries.".format(jbop))
            exit()

    return keys_list


def share_playlists(playlist_titles, users):
    """
    Parameters
    ----------
    playlist_titles: list
        list of playlist titles
    users: list
        list of user names
    """
    for user in users:
        for title in playlist_titles:
            logger.info("...Shared {title} playlist to '{user}'.".format(title=title, user=user))
            plex.playlist(title).copyToUser(user)

    exit()


def show_playlist(playlist_title, playlist_keys):
    """
    Parameters
    ----------
    playlist_title: str
        playlist's title
    playlist_keys: list
        list of rating keys for playlist
    """
    playlist_list = []
    for key in playlist_keys:
        # todo-me add try to catch when Tautulli reports a rating key that is now missing from Plex
        plex_obj = plex.fetchItem(key)
        if plex_obj.type == 'show':
            for episode in plex_obj.episodes():
                title = u"{}".format(episode._prettyfilename())
                title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').translate(None, "'")
                playlist_list.append(title)
        else:
            title = u"{} ({})".format(plex_obj._prettyfilename(), plex_obj.year)
            title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').translate(None, "'")
            playlist_list.append(title)

    logger.info(u"Contents of Playlist {title}:\n{playlist}".format(
        title=playlist_title,
        playlist=', '.join(playlist_list)))
    exit()


def create_playlist(playlist_title, playlist_keys, server, user):
    """
    Parameters
    ----------
    playlist_title: str
        playlist title
    playlist_keys: list
        list of rating keys for playlist
    server: class
        server instance
    user: str
        users name
    """
    playlist_list = []
    for key in playlist_keys:
        try:
            plex_obj = server.fetchItem(key)
            if plex_obj.type == 'show':
                for episode in plex_obj.episodes():
                    playlist_list.append(episode)
            else:
                playlist_list.append(plex_obj)
        except Exception:
            try:
                obj = plex.fetchItem(key)
                logger.exception("{} may not have permission to this title: {}".format(user, obj.title))
                pass
            except Exception:
                logger.exception('Rating Key: {}, may have been deleted or moved.'.format(key))

    if playlist_list:
        server.createPlaylist(playlist_title, playlist_list)
        logger.info("...Added Playlist: {title} to '{user}'.".format(title=playlist_title, user=user))


def delete_playlist(playlist_dict, title):
    """
    Parameters
    ----------
    playlist_dict: dict
        Server and user information
    title: str, list
        Playlist title(s)
    """
    server = playlist_dict['server']
    user = playlist_dict['user']

    try:
        # todo-me this needs improvement
        for playlist in server.playlists():
            if isinstance(title, str):
                # If str then updating playlist
                if playlist.title == title:
                    playlist.delete()
                    logger.info("...Deleted Playlist: {playlist.title} for '{user}'."
                          .format(playlist=playlist, user=user))
            if isinstance(title, list):
                # If list then removing selected playlists
                if playlist.title in title:
                    playlist.delete()
                    logger.info("...Deleted Playlist: {playlist.title} for '{user}'."
                          .format(playlist=playlist, user=user))

    except Exception:
        logger.exception("Playlist not found on '{user}' account".format(user=user))
        pass


def create_title(jbop, libraries, days, filters, search, limit):
    """

    Parameters
    ----------
    jbop: str
        Playlist selector
    libraries: dict
        Plex libraries information
    days: int
        Amount of days for Popular media types
    filters: dict
        Plex media filters
    search: dict
        Search terms
    limit
        Playlist size limit

    Returns
    -------
    title
    """
    title = ''
    if jbop == 'historyToday':
        title = selectors()['historyToday'].format(month=today.month, day=today.day)

    elif jbop == 'historyWeek':
        title = selectors()['historyWeek'].format(week=weeknum)

    elif jbop == 'historyMonth':
        title = selectors()['historyMonth'].format(month=today.strftime("%B"))

    elif jbop == 'custom':
        if search and not filters:
            title_lst = []
            for values in search.values():
                if isinstance(values, list):
                    title_lst += values
                else:
                    title_lst += [values]
            title = " ".join(title_lst)
        elif filters and not search:
            title_lst = []
            for values in filters.values():
                if isinstance(values, list):
                    title_lst += values
                else:
                    title_lst += [values]
            title = " ".join(title_lst)
        elif search and filters:
            search_title = ' '.join(search.values())
            filters_title = ' '.join(filters.values())
            title = filters_title + ' ' + search_title
        # Capitalize each word in title
        title = " ".join(word.capitalize() for word in title.split())
        title = selectors()['custom'].format(custom=title)

    elif jbop == 'random':
        if not limit:
            logger.info("Random selector needs a limit. Use --limit.")
            exit()
        title = selectors()['random'].format(count=limit, libraries='/'.join(libraries.values()))

    elif jbop == 'popularTv':
        title = selectors()['popularTv'].format(days=days)
    elif jbop == 'popularMovies':
        title = selectors()['popularMovies'].format(days=days)

    return title


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create, share, and clean Playlists for users.",
        formatter_class=argparse.RawTextHelpFormatter)
    # todo-me use parser grouping instead of choices for action and jbop?
    parser.add_argument('--jbop', choices=selectors().keys(), metavar='',
                        help='Playlist selector.\n'
                             'Choices: (%(choices)s)')
    parser.add_argument('--action', required=True, choices=actions(),
                        help='Action selector.'
                             '{}'.format(actions.__doc__))
    parser.add_argument('--user', nargs='+', choices=user_lst, metavar='',
                        help='The Plex usernames to create/share to or delete from. Allowed names are:\n'
                             'Choices: %(choices)s')
    parser.add_argument('--allUsers', default=False, action='store_true',
                        help='Select all users.')
    parser.add_argument('--libraries', nargs='+', choices=sections_dict.values(), metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are:\n'
                             'Choices: %(choices)s')
    parser.add_argument('--allLibraries', default=False, action='store_true',
                        help='Select all libraries.')
    parser.add_argument('--self', default=False, action='store_true',
                        help='Create playlist for admin.\n'
                             'Default: %(default)s')
    parser.add_argument('--days', type=str, default=DAYS,
                        help='The time range to calculate statistics.\n'
                             'Default: %(default)s')
    parser.add_argument('--top', type=str, default=TOP,
                        help='The number of top items to list.\n'
                             'Default: %(default)s')
    parser.add_argument('--playlists', nargs='+', metavar='',
                        help='Enter Playlist name to be managed.')
    parser.add_argument('--allPlaylists', default=False, action='store_true',
                        help='Select all playlists.')
    parser.add_argument('--name', type=str,
                        help='Custom name for playlist.')
    parser.add_argument('--limit', type=int, default=False,
                        help='Limit the amount items to be added to a playlist.')
    parser.add_argument('--filter', action='append', type=lambda kv: kv.split("="),
                        help='Search filtered metadata fields.\n'
                             'Filters: ({}).'.format(', '.join(filters_lst)))
    parser.add_argument('--search', action='append', type=lambda kv: kv.split("="),
                        help='Search non-filtered metadata fields for keywords '
                             'in title, summary, etc.')

    opts = parser.parse_args()

    title = ''
    search = ''
    filters = ''
    playlists = []
    keys_list = []
    playlist_dict = {'data': []}

    if opts.search:
        search = dict(opts.search)
        for k, v in search.items():
            # If comma separated search then consider searching values with AND statement
            if "," in v:
                search[k] = v.split(",")
    if opts.filter:
        if len(opts.filter) >= 2:
            # Check if filter key was used twice or more
            filter_key = opts.filter[0][0]
            filter_count = sum(f.count(filter_key) for f in opts.filter)
            # If filter key used more than once than consider filtering values with OR statement
            if filter_count > 1:
                filters_lst = []

        filters = dict(opts.filter)
        for k, v in filters.items():
            # If comma separated filter then consider filtering values with AND statement
            if "," in v:
                filters[k] = v.split(",")
        # Check if provided filter exist, exit if it doesn't exist
        if not (set(filters.keys()) & set(filters_lst)):
            logger.error('({}) was not found in filters list: [{}]'
                  .format(' '.join(filters.keys()), ', '.join(filters_lst)))
            exit()

    # Defining users
    users = exclusions(opts.allUsers, opts.user, user_lst)

    # Defining libraries
    libraries = exclusions(opts.allLibraries, opts.libraries, sections_dict)

    # Defining selected playlists
    selected_playlists = exclusions(opts.allPlaylists, opts.playlists, playlist_lst)

    # Create user server objects
    if users:
        for user in users:
            # todo-me smart playlists will have to recreated in users server instance
            if opts.action == 'share' and selected_playlists:
                logger.info("Sharing playlist(s)...")
                share_playlists(selected_playlists, users)
            user_acct = account.user(user)
            user_server = PlexServer(PLEX_URL, user_acct.get_token(plex.machineIdentifier))
            all_playlists = [pl.title for pl in user_server.playlists()]
            user_selected = exclusions(opts.allPlaylists, opts.playlists, all_playlists)
            playlist_dict['data'].append({
                'server': user_server,
                'user': user,
                'user_selected': user_selected,
                'all_playlists': all_playlists})

    if opts.self or not users:
        playlist_dict['data'].append({
            'server': plex,
            'user': 'admin',
            'user_selected': selected_playlists,
            'all_playlists': playlist_lst})

    if not opts.jbop and opts.action == 'show':
        logger.info("Displaying the user's playlist(s)...")
        for data in playlist_dict['data']:
            user = data['user']
            playlists = data['all_playlists']
            logger.info("{}'s current playlist(s): {}".format(user, ', '.join(playlists)))
        exit()

    if libraries:
        title = create_title(opts.jbop, libraries, opts.days, filters, search, opts.limit)
        keys_list = build_playlist(opts.jbop, libraries, opts.days, opts.top, filters, search, opts.limit)

    # Remove or build playlists
    if opts.action == 'remove':
        logger.info("Deleting the playlist(s)...")
        for data in playlist_dict['data']:
            titles = data['user_selected']
            delete_playlist(data, titles)

    # Check if limit exist and if it's greater than the pulled list of rating keys
    if opts.limit and len(keys_list) > int(opts.limit):
        if opts.jbop == 'random':
            keys_list = random.sample((keys_list), opts.limit)
        else:
            keys_list = keys_list[:opts.limit]

    # Setting custom name if provided
    if opts.name:
        title = opts.name

    if opts.jbop and opts.action == 'show':
        if len(libraries) > 0:
            show_playlist(title, keys_list)
        else:
            logger.error("Missing --libraries or --allLibraries")
            exit()

    if opts.action == 'update':
        logger.info("Deleting the playlist(s)...")
        for data in playlist_dict['data']:
            delete_playlist(data, title)
            logger.info('Creating playlist(s)...')
        for data in playlist_dict['data']:
            create_playlist(title, keys_list, data['server'], data['user'])

    if opts.action == 'add':
        logger.info('Creating playlist(s)...')
        for data in playlist_dict['data']:
            create_playlist(title, keys_list, data['server'], data['user'])

    logger.info("Done.")
