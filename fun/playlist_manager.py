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
  --action {add,remove,update,show,share}
                        Action selector.
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
  --self                Create playlist for admin.
                        Default: False
  --days DAYS           The time range to calculate statistics.
                        Default: 30
  --top TOP             The number of top items to list.
                        Default: 5
   --playlists          Space separated list of case sensitive names to
                        process. Allowed names are:
                        Choices: (PLAYLISTS)


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
    
 Show 5 Most Popular TV Shows (30 days) Playlist
    python playlist_manager.py --jbop mostPopularTv --action show
    
 Show all users current playlists
    python playlist_manager.py --action show --allUsers
    
 Share existing admin Playlists "My Custom Playlist" and "Another Playlist" with all users
    python playlist_manager.py --action share --allUsers --playlists "My Custom Playlist" "Another Playlist"
 Excluding;

 --user becomes excluded if --allUsers is set
   python playlist_manager.py --action show --allUsers --user USER
       - Show all users current Playlists... all users but USER

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


def actions():
    """
    add - create new playlist for admin or users
    remove - remove playlist type or name from admin or users
    update - remove playlist type and create new playlist type for admin or users
    show - show contents of playlist type or admin or users current playlists
    share - share existing playlist by title from admin to users
    """
    return ['add', 'remove', 'update', 'show', 'share']


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


def sort_by_dates(video):
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
        ad_week = int(datetime.date(ad_year, ad_month, ad_day).strftime("%V"))

        if ad_month == today.month and ad_day == today.day:
            # todo-me return object
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
                if sort_by_dates(child):
                    item_date = sort_by_dates(child)
                    child_lst += item_date
            elif child.type == 'show':
                for episode in child.episodes():
                    if sort_by_dates(episode):
                        item_date = sort_by_dates(episode)
                        child_lst += item_date
            else:
                pass

    # Sort by original air date, oldest first
    # todo-me move sorting and add more sorting options
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
        print("...Added {title} playlist to '{user}'.".format(title=playlist_title, user=user))


def delete_playlist(playlist_dict):
    """

    Parameters
    ----------
    playlist_dict

    Returns
    -------

    """

    server = playlist_dict['server']
    jbop = playlist_dict['jbop']
    user = playlist_dict['user']
    pop_movie = playlist_dict['pop_movie']
    pop_tv = playlist_dict['pop_tv']
    
    try:
        for playlist in server.playlists():
            if jbop == 'todayInHistory':
                if playlist.title.startswith('Aired Today'):
                    playlist.delete()
                    print("...Deleted {playlist.title} for '{user}'."
                          .format(playlist=playlist, user=user))
            elif jbop == 'mostPopularMovies':
                if playlist.title == pop_movie:
                    playlist.delete()
                    print("...Deleted {playlist.title} for '{user}'."
                          .format(playlist=playlist, user=user))
            elif jbop == 'mostPopularTv':
                if playlist.title == pop_tv:
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
    parser.add_argument('--jbop', choices=SELECTOR, metavar='',
                        help='Playlist selector.\n'
                             'Choices: (%(choices)s)')
    parser.add_argument('--action', required=True, choices=actions(),
                        help='Action selector.'
                             '{}'.format(actions.__doc__))
    parser.add_argument('--user', nargs='+', choices=user_lst, metavar='',
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
    parser.add_argument('--playlists', nargs='+', choices=playlist_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             'Choices: %(choices)s')
    parser.add_argument('--name', type=str,
                        help='Custom name for playlist.')
    parser.add_argument('--limit', type=int, default=False,
                        help='Limit the amount items to be added to a playlist.')
    # todo-me custom naming for playlists --name?
    # todo-me custom limits to playlist --limit?
    opts = parser.parse_args()
    # print(opts)

    users = ''
    plex_servers = []
    pop_movie_title = MOVIE_PLAYLIST.format(days=opts.days)
    pop_tv_title = TV_PLAYLIST.format(days=opts.days)
    
    playlist_dict = {'jbop': opts.jbop,
                     'pop_tv': pop_tv_title,
                     'pop_movie': pop_movie_title}

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
            playlist_dict['server'] = x['server']
            playlist_dict['user'] = x['user']
            delete_playlist(playlist_dict)

    else:
        # todo-me add more playlist types
        # todo-me random, genre, rating, unwatched, studio, network (shows),
        # todo-me labels, collections, country, writer, director,
        if opts.jbop == 'todayInHistory':
            try:
                keys_list = get_all_content(opts.libraries)
            except TypeError as e:
                print("Libraries are not defined for {}. Use --libraries.".format(opts.jbop))
                exit("Error: {}".format(e))
            title = TODAY_PLAY_TITLE.format(month=today.month, day=today.day)

        if opts.jbop == 'mostPopularTv':
            home_stats = get_home_stats(opts.days, opts.top)
            for stat in home_stats:
                if stat['stat_id'] == 'popular_tv':
                    keys_list = [x['rating_key'] for x in stat['rows']]
                    title = pop_tv_title


        if opts.jbop == 'mostPopularMovies':
            home_stats = get_home_stats(opts.days, opts.top)
            for stat in home_stats:
                if stat['stat_id'] == 'popular_movies':
                    keys_list = [x['rating_key'] for x in stat['rows']]
                    title = pop_movie_title

        if opts.jbop and opts.action == 'show':
            show_playlist(title, keys_list)

    if opts.action == 'update':
        print("Deleting the playlist(s)...")
        for x in plex_servers:
            playlist_dict['server'] = x['server']
            playlist_dict['user'] = x['user']
            delete_playlist(playlist_dict)
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
