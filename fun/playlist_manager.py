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
    
 Excluding;

 --user becomes excluded if --allUsers is set
   python playlist_manager.py --action show --allUsers --user USER
       - Show all users current Playlists... all users but USER

 --libraries becomes excluded if --allLibraries is set
   python playlist_manager.py --jbop historyToday --allLibraries --libraries Movies --action add
       - Create Aired Today Playlist from every library by Movies for admin user

"""

import sys
import random
import requests
import argparse
import operator
import datetime
import unicodedata
from plexapi.server import PlexServer, CONFIG

### EDIT SETTINGS ###

PLEX_URL = ''
PLEX_TOKEN = ''
TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''

## CODE BELOW ##

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

user_lst = [x.title for x in plex.myPlexAccount().users() if x.servers]
sections = plex.library.sections()
sections_dict = {x.key: x.title for x in sections}
filter_lst = list(set([y for x in sections if x.type != 'photo' for y in x.ALLOWED_FILTERS]))
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
    selections = {'historyToday':'Aired Today {month}-{day} in History',
                  'historyWeek': 'Aired This Week ({week}) in History',
                  'historyMonth': 'Aired in {month}',
                  'popularTv': 'Most Popular TV Shows ({days} days)',
                  'popularMovies': 'Most Popular Movies ({days} days)',
                  'custom':'{custom} Playlist',
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
               'stats_type': 0} # stats_type = plays

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
        if date_type == 'historyWeek':
            if ad_week == weeknum:
                return [[video.ratingKey] + [str(video.originallyAvailableAt)]]
        if date_type == 'historyMonth':
            if ad_month == today.month:
                return [[video.ratingKey] + [str(video.originallyAvailableAt)]]

    # todo-me return object
    except Exception as e:
        # print(e)
        return


def get_content(libraries, jbop, filters=None, search=None, limit=None):
    """Get all movies or episodes from LIBRARY_NAME

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
    keyword = ''

    if search or filters:
        if search:
            # todo-me replace with documentation showing the available search operators
            keyword = {key + '__icontains': value for key, value in search.items()}
        # Loop through each library
        for library in libraries.keys():
            plex_library = plex.library.sectionByID(library)
            library_type = plex_library.type
            # Find media type, if show then search/filter episodes
            if library_type == 'movie':
                # Decisions to stack filter and search
                if keyword:
                    search_lst = [movie.ratingKey for movie in plex_library.all(**keyword)]
                    child_lst += search_lst
                if filters:
                    filter_lst = [movie.ratingKey for movie in plex_library.search(**filters)]
                    child_lst += filter_lst
                if keyword and filters:
                    child_lst += list(set(filter_lst) & set(search_lst))
                    
            elif library_type == 'show':
                # Decisions to stack filter and search
                if keyword:
                    for show in plex_library.all():
                        for episode in show.episodes(**keyword):
                            search_lst += [episode.ratingKey]
                    child_lst += search_lst
                if filters:
                    for show in plex_library.search(**filters):
                        for episode in show.episodes():
                            filter_lst += [episode.ratingKey]
                    child_lst += filter_lst
                if keyword and filters:
                    child_lst += list(set(filter_lst) & set(search_lst))
            else:
                pass
        # Keep only results found from both search and filters
        if keyword and filters:
            child_lst = list(set(i for i in child_lst if child_lst.count(i) > 1))
            
        play_lst = child_lst
        
    else:
        for library in libraries.keys():
            plex_library = plex.library.sectionByID(library)
            library_type = plex_library.type
            if jbop == 'random' and library_type == 'movie':
                child_lst += [movie.ratingKey for movie in random.sample((plex_library.all()), limit)]
            elif jbop == 'random' and library_type == 'show':
                all_eps = [eps for show in plex_library.all() for eps in show.episodes()]
                child_lst += [show.ratingKey for show in random.sample((all_eps), limit)]
            else:
                for child in plex_library.all():
                    if child.type == 'movie':
                        if sort_by_dates(child, jbop):
                            item_date = sort_by_dates(child, jbop)
                            child_lst += item_date
                    elif child.type == 'show':
                        for episode in child.episodes():
                            if sort_by_dates(episode, jbop):
                                item_date = sort_by_dates(episode, jbop)
                                child_lst += item_date
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
            print("Libraries are not defined for {}. Use --libraries.".format(jbop))
            exit("Error: {}".format(e))

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
            print("...Shared {title} playlist to '{user}'.".format(title=title, user=user))
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

    print(u"Contents of Playlist {title}:\n{playlist}".format(title=playlist_title,
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
        except Exception as e:
            try:
                obj = plex.fetchItem(key)
                print("{} may not have permission to this title: {}".format(user, obj.title))
                # print("Error: {}".format(e))
                pass
            except Exception as e:
                print('Rating Key: {}, may have been deleted or moved.'.format(key))
                # print("Error: {}".format(e))

    if playlist_list:
        server.createPlaylist(playlist_title, playlist_list)
        print("...Added Playlist: {title} to '{user}'.".format(title=playlist_title, user=user))


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
                    print("...Deleted Playlist: {playlist.title} for '{user}'."
                          .format(playlist=playlist, user=user))
            if isinstance(title, list):
                # If list then removing selected playlists
                if playlist.title in title:
                    playlist.delete()
                    print("...Deleted Playlist: {playlist.title} for '{user}'."
                          .format(playlist=playlist, user=user))

    except:
        # print("Playlist not found on '{user}' account".format(user=user))
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
            title = ' '.join(search.values())
        elif filters and not search:
            title = ' '.join(filters.values())
        elif search and filters:
            search_title = ' '.join(search.values())
            filters_title = ' '.join(filters.values())
            title = filters_title + ' ' + search_title
        # Capitalize each word in title
        title = " ".join(word.capitalize() for word in title.split())
        title = selectors()['custom'].format(custom=title)

    elif jbop == 'random':
        if not limit:
            print("Random selector needs a limit. Use --limit.")
            exit()
        title = selectors()['random'].format(count=limit, libraries='/'.join(libraries.values()))

    if jbop in ['popularTv', 'popularMovies']:
        if jbop == 'popularTv':
            title = selectors()['popularTv'].format(days=days)
        if jbop == 'popularMovies':
            title = selectors()['popularMovies'].format(days=days)

    return title


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Create, share, and clean Playlists for users.",
                                     formatter_class = argparse.RawTextHelpFormatter)
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
                             'Filters: ({}).'.format(', '.join(filter_lst)))
    parser.add_argument('--search', type=lambda kv: kv.split("="),
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
        search = dict([opts.search])
    if opts.filter:
        filters = dict(opts.filter)
        # Check if provided filter exist, exit if it doesn't exist
        if not (set(filters.keys()) & set(filter_lst)):
            print('({}) was not found in filters list: [{}]'
                  .format(' '.join(filters.keys()), ', '.join(filter_lst)))
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
                print("Sharing playlist(s)...")
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
        playlist_dict['data'].append({'server': plex,
                             'user': 'admin',
                             'user_selected': selected_playlists,
                             'all_playlists': playlist_lst})

    if not opts.jbop and opts.action == 'show':
        print("Displaying the user's playlist(s)...")
        for data in playlist_dict['data']:
            user = data['user']
            playlists = data['all_playlists']
            print("{}'s current playlist(s): {}".format(user, ', '.join(playlists)))
        exit()
    
    if libraries:
        title = create_title(opts.jbop, libraries, opts.days, filters, search, opts.limit)
        keys_list = build_playlist(opts.jbop, libraries, opts.days, opts.top, filters, search, opts.limit)

    # Remove or build playlists
    if opts.action == 'remove':
        print("Deleting the playlist(s)...")
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
        show_playlist(title, keys_list)

    if opts.action == 'update':
        print("Deleting the playlist(s)...")
        for data in playlist_dict['data']:
            delete_playlist(data, title)
        print('Creating playlist(s)...')
        for data in playlist_dict['data']:
            create_playlist(title, keys_list, data['server'], data['user'])
            
    if opts.action == 'add':
        print('Creating playlist(s)...')
        for data in playlist_dict['data']:
            create_playlist(title, keys_list, data['server'], data['user'])

    print("Done.")
