"""
Description: Create and share playlists based on Most Popular TV/Movies from Tautulli
                and Aired this day in history.
Author: blacktwin
Requires: requests, plexapi

Create, share, and clean Playlists for users.

optional arguments:
  -h, --help            show this help message and exit
  --jbop                Playlist selector.
                        Choices: (todayInHistory, mostPopularTv, mostPopularMovies)
  --action              Action selector.
                        Choices: (add, remove, update)
  --users {]            The Plex usernames to create/share to or delete from.
                        Choices:  (USERNAMES)
  --libraries  [ ...]   Space separated list of case sensitive names to
                        process. Allowed names are:
                        Choices: (LIBRARIES)
  --self                Create playlist for admin.
                        Default: False
  --days DAYS           The time range to calculate statistics.
                        Default: 30
  --top TOP             The number of top items to list.
                        Default: 5


 Example:
    Use with cron or task to schedule runs
    
 Create Aired Today Playlist from Movies and TV Shows libraries for admin user
    python playlist_manager.py --jbop todayInHistory --libraries Movies "TV Shows" --action add

 Create Aired Today Playlist from Movies and TV Shows libraries and share to users bob, Black Twin and admin user
    python playlist_manager.py --jbop todayInHistory --libraries Movies "TV Shows" --action add --users bob "Black Twin" --self

 Update previous Aired Today Playlist(s) from Movies and TV Shows libraries and share to users bob and Black Twin
    python playlist_manager.py --jbop todayInHistory --libraries Movies "TV Shows" --action update --users bob "Black Twin"

 Delete all previous Aired Today Playlist(s) from users bob and Black Twin
    python playlist_manager.py --jbop todayInHistory --action remove --users bob "Black Twin"

 Create 5 Most Popular TV Shows (30 days) Playlist and share to users bob and Black Twin
    python playlist_manager.py --jbop mostPopularTv --action add --users bob "Black Twin"

 Create 10 Most Popular Movies (60 days) Playlist and share to users bob and Black Twin
    python playlist_manager.py --jbop mostPopularMovies --action add --users bob "Black Twin" --days 60 --top 10
"""

import sys
import requests
import argparse
import operator
import datetime
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

# Playlist Titles
TODAY_PLAY_TITLE = 'Aired Today {month}-{day}'
MOVIE_PLAYLIST = 'Most Popular Movies ({days} days)'
TV_PLAYLIST = 'Most Popular TV Shows ({days} days)'

SELECTOR = ['todayInHistory', 'mostPopularTv', 'mostPopularMovies']

ACTIONS = ['add', 'remove', 'update', 'show', 'share']
"""
add - create new playlist for admin or users
remove - remove playlist type or name from admin or users
update - remove playlist type and create new playlist type for admin or users
show - show contents of playlist type
share - share existing playlist by title from admin to users
"""

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

user_lst = [x.title for x in plex.myPlexAccount().users()]
section_lst = [x.title for x in plex.library.sections()]
playlist_lst = [x.title for x in plex.playlists()]
today = datetime.datetime.now().date()


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


def find_air_dates(video):
    """Find what aired with today's month-day

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
        ad_month = str(video.originallyAvailableAt.month)
        ad_day = str(video.originallyAvailableAt.day)

        if ad_month == str(today.month) and ad_day == str(today.day):
            return [[video.ratingKey] + [str(video.originallyAvailableAt)]]
    except Exception as e:
        # print(e)
        return


def get_all_content(library_name):
    """Get all movies or episodes from LIBRARY_NAME

    Parameters
    ----------
    library_name: list
        list of library objects

    Returns
    -------
    list
        Sorted list of Movie and episodes that
        aired on today's date.

    """

    child_lst = []

    for library in library_name:
        for child in plex.library.section(library).all():
            if child.type == 'movie':
                if find_air_dates(child):
                    item_date = find_air_dates(child)
                    child_lst += item_date
            elif child.type == 'show':
                for episode in child.episodes():
                    if find_air_dates(episode):
                        item_date = find_air_dates(episode)
                        child_lst += item_date
            else:
                pass

    # Sort by original air date, oldest first
    aired_lst = sorted(child_lst, key=operator.itemgetter(1))

    # Remove date used for sorting
    play_lst = [x[0] for x in aired_lst]

    return play_lst


def share_playlists(playlist_titles, users):
    """

    Parameters
    ----------
    playlist_titles
    users

    Returns
    -------

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
    playlist_keys

    Returns
    -------

    """
    playlist_list = []
    for key in playlist_keys:
        plex_obj = plex.fetchItem(key)
        if plex_obj.type == 'show':
            for episode in plex_obj.episodes():
                title = "{}".format(episode._prettyfilename())
                playlist_list.append(title)
        else:
            title = "{} ({})".format(plex_obj.title, plex_obj.year)
            playlist_list.append(title)

    print("Contents of Playlist {title}:\n{playlist}".format(title=playlist_title,
                                                             playlist=', '.join(playlist_list)))
    exit()
    
    
def create_playlist(playlist_title, playlist_keys, server, user):
    """

    Parameters
    ----------
    playlist_title
    playlist_keys
    server
    user

    Returns
    -------

    """
    playlist_list = []
    for key in playlist_keys:
        plex_obj = server.fetchItem(key)
        if plex_obj.type == 'show':
            for episode in plex_obj.episodes():
                playlist_list.append(episode)
        else:
            playlist_list.append(plex_obj)

    server.createPlaylist(playlist_title, playlist_list)
    print("...Added {title} playlist to '{user}'.".format(title=playlist_title, user=user))


def delete_playlist(server, user, jbop):
    """

    Parameters
    ----------
    user_lst

    Returns
    -------

    """

    # Delete the old playlist
    try:
        for playlist in server.playlists():
            if jbop == 'todayInHistory':
                if playlist.title.startswith('Aired Today'):
                    playlist.delete()
                    print("...Deleted {playlist.title} for '{user}'."
                          .format(playlist=playlist, user=user))
            elif jbop == 'mostPopularMovies':
                if playlist.title.startswith('Most Popular Movies'):
                    playlist.delete()
                    print("...Deleted {playlist.title} for '{user}'."
                          .format(playlist=playlist, user=user))
            elif jbop == 'mostPopularTv':
                if playlist.title.startswith('Most Popular TV'):
                    playlist.delete()
                    print("...Deleted {playlist.title} for '{user}'."
                          .format(playlist=playlist, user=user))

    except:
        # print("Playlist not found on '{user}' account".format(user=user))
        pass


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Create, share, and clean Playlists for users.",
                                     formatter_class = argparse.RawTextHelpFormatter)
    # todo-me use parser grouping instead of choices for action and jbop?
    parser.add_argument('--jbop', choices=SELECTOR,
                        help='Playlist selector.\n'
                             'Choices: (%(choices)s)')
    parser.add_argument('--action', required=True, choices=ACTIONS,
                        help='Action selector.\n'
                             'Choices: (%(choices)s)')
    parser.add_argument('--user', nargs='+', choices=user_lst,
                        help='The Plex usernames to create/share to or delete from. Allowed names are: \n'
                             'Choices: %(choices)s')
    parser.add_argument('--allUsers', default=False, action='store_true',
                        help='Select all users.')
    parser.add_argument('--libraries', nargs='+', choices=section_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             'Choices: %(choices)s')
    parser.add_argument('--self', default=False, action='store_true',
                        help='Create playlist for admin. \n'
                             'Default: %(default)s')
    parser.add_argument('--days', type=str, default=DAYS,
                        help='The time range to calculate statistics. \n'
                             'Default: %(default)s')
    parser.add_argument('--top', type=str, default=TOP,
                        help='The number of top items to list. \n'
                             'Default: %(default)s')
    parser.add_argument('--playlists', nargs='+', choices=playlist_lst,
                        help='Shows in playlist to be removed from On Deck')
    
    opts = parser.parse_args()
    # print(opts)

    users = ''
    plex_servers = []

    # Defining users
    if opts.allUsers and not opts.user:
        users = user_lst
    elif not opts.allUsers and opts.user:
        users = opts.user
    elif opts.allUsers and opts.user:
        # If allUsers is used then any users listed will be excluded
        for user in opts.user:
            user_lst.remove(user)
            users = user_lst
            
    if users:
        for user in users:
            if opts.action == 'share':
                print("Sharing playlist(s)...")
                share_playlists(opts.playlists, users)
            user_acct = account.user(user)
            plex_servers.append({
                'server': PlexServer(PLEX_URL, user_acct.get_token(plex.machineIdentifier)),
                'user': user})
        if opts.self:
            plex_servers.append({'server': plex,
                                 'user': 'admin'})
    else:
        plex_servers.append({'server': plex,
                            'user': 'admin'})
            
    if opts.action == 'remove':
        print("Deleting the playlist(s)...")
        for x in plex_servers:
            delete_playlist(x['server'], x['user'], opts.jbop)

    else:
        # todo-me add more playlist types
        if opts.jbop == 'todayInHistory':
            try:
                keys_list = get_all_content(opts.libraries)
            except TypeError as e:
                print("Libraries are not defined for {}. Use --libraries.".format(opts.jbop))
                exit(e)
            title = TODAY_PLAY_TITLE.format(month=today.month, day=today.day)

        if opts.jbop == 'mostPopularTv':
            home_stats = get_home_stats(opts.days, opts.top)
            for stat in home_stats:
                if stat['stat_id'] == 'popular_tv':
                    keys_list = [x['rating_key'] for x in stat['rows']]
                    title = TV_PLAYLIST.format(days=opts.days)

        if opts.jbop == 'mostPopularMovies':
            home_stats = get_home_stats(opts.days, opts.top)
            for stat in home_stats:
                if stat['stat_id'] == 'popular_movies':
                    keys_list = [x['rating_key'] for x in stat['rows']]
                    title = MOVIE_PLAYLIST.format(days=opts.days)

        if opts.jbop and opts.action == 'show':
            show_playlist(title, keys_list)

    if opts.action == 'update':
        print("Deleting the playlist(s)...")
        for x in plex_servers:
            delete_playlist(x['server'], x['user'], opts.jbop)
        print('Creating playlist(s)...')
        for x in plex_servers:
            create_playlist(title, keys_list, x['server'], x['user'])
            
    # todo-me allow for update or another action to remove watched items
    # todo-me use Tautulli to imitate Smart Playlist

    if opts.action == 'add':
        print('Creating playlist(s)...')
        for x in plex_servers:
            create_playlist(title, keys_list, x['server'], x['user'])

    if opts.action == 'show':
        print("Displaying the user's playlist(s)...")
        for x in plex_servers:
            user = x['user']
            playlist = [y.title for y in x['server'].playlists()]
            print("{}'s current playlist(s): {}".format(user, ', '.join(playlist)))

    print("Done.")
