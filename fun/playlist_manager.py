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

"""

import sys
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

user_lst = [x.title for x in plex.myPlexAccount().users()]
section_lst = [x.title for x in plex.library.sections()]
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
    """Playlist selections and titles
    """
    selections = {'historyToday':'Aired Today {month}-{day} in History',
                  'historyWeek': 'Aired This Week ({week}) in History',
                  'historyMonth': 'Aired in {month}',
                  'popularTv': 'Most Popular TV Shows ({days} days)',
                  'popularMovies': 'Most Popular Movies ({days} days)',
                  'keyword':'{keyword} Playlist',
                  'genre': '{title} Playlist',
                  'random': '{count} Random Playlist',
                  'studio': 'Studio: {title} Playlist',
                  'network': 'Network: {title} Playlist',
                  'labels': 'Labels: {title} Playlist',
                  'collections': 'Collections: {title} Playlist',
                  'country': 'Country: {title} Playlist',
                  'writer': 'Writer: {title} Playlist',
                  'director': 'Director: {title} Playlist',
                  'actor': 'Actor: {title} Playlist'}
    
    return selections

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


def get_content(library_name, jbop, search=None):
    """Get all movies or episodes from LIBRARY_NAME

    Parameters
    ----------
    library_name: list
        list of library objects
    jbop: str
        jbop value for searching

    Returns
    -------
    list
        Sorted list of Movie and episodes that
        aired on today's date.
    """
    # todo-me expand function for keyword searching
    child_lst = []
    if search and jbop == 'keyword':
        if search.keys()[0] in selectors().keys():
            searchable = True
            keyword = search
        else:
            searchable = False
            keyword = {key + '__icontains': value for key, value in search.items()}

        for library in library_name:
            plex_library = plex.library.section(library)
            library_type = plex_library.type
            if library_type == 'movie':
                if searchable:
                    child_lst = [x.ratingKey for x in plex_library.search(**keyword)]
                else:
                    child_lst = [x.ratingKey for x in plex_library.all(**keyword)]
            elif library_type == 'show':
                if searchable:
                    for child in plex_library.search(**keyword):
                        child_lst += [child.ratingKey]
                else:
                    child = plex_library.all()
                    for episode in child.episodes(**keyword):
                        child_lst += [episode.ratingKey]
            else:
                pass
        play_lst = child_lst

    else:
        for library in library_name:
            for child in plex.library.section(library).all():
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

        # Sort by original air date, oldest first
        # todo-me move sorting and add more sorting options
        aired_lst = sorted(child_lst, key=operator.itemgetter(1))
    
        # Remove date used for sorting
        play_lst = [x[0] for x in aired_lst]

    return play_lst


def build_playlist(jbop, libraries=None, days=None, top=None, search=None):
    """
    Parameters
    ----------
    jbop: str
        The predefined Playlist type
    libraries: list
        Libraries to use to build Playlist
    days: int
        Days to search for Top Movies/Tv Shows
    top: int
        Limit to search for Top Movies/Tv Shows

    Returns
    -------
    key_list, title

    """
    keys_list = []
    title = ''
    if jbop == 'historyToday':
        try:
            keys_list = get_content(libraries, jbop)
        except TypeError as e:
            print("Libraries are not defined for {}. Use --libraries.".format(jbop))
            exit("Error: {}".format(e))
        title = selectors()['historyToday'].format(month=today.month, day=today.day)
    
    elif jbop == 'historyWeek':
        try:
            keys_list = get_content(libraries, jbop)
        except TypeError as e:
            print("Libraries are not defined for {}. Use --libraries.".format(jbop))
            exit("Error: {}".format(e))
        title = selectors()['historyWeek'].format(week=weeknum)

    elif jbop == 'historyMonth':
        try:
            keys_list = get_content(libraries, jbop)
        except TypeError as e:
            print("Libraries are not defined for {}. Use --libraries.".format(jbop))
            exit("Error: {}".format(e))
        title = selectors()['historyMonth'].format(month=today.strftime("%B"))
        
    elif jbop == 'keyword':
        try:
            keys_list = get_content(libraries, jbop, search)
        except TypeError as e:
            print("Libraries are not defined for {}. Use --libraries.".format(jbop))
            exit("Error: {}".format(e))
        title = selectors()['keyword'].format(keyword=' '.join(search.values()).capitalize())
    
    elif jbop == 'popularTv':
        home_stats = get_home_stats(days, top)
        for stat in home_stats:
            if stat['stat_id'] == 'popular_tv':
                keys_list = [x['rating_key'] for x in stat['rows']]
                title = pop_tv_title
    
    elif jbop == 'popularMovies':
        home_stats = get_home_stats(days, top)
        for stat in home_stats:
            if stat['stat_id'] == 'popular_movies':
                keys_list = [x['rating_key'] for x in stat['rows']]
                title = pop_movie_title

    return keys_list, title


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
    """
    playlist_list = []
    for key in playlist_keys:
        plex_obj = plex.fetchItem(key)
        if plex_obj.type == 'show':
            for episode in plex_obj.episodes():
                title = "{}".format(episode._prettyfilename())
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
    playlist_title
    playlist_keys
    server
    user
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
    """

    server = playlist_dict['server']
    jbop = playlist_dict['jbop']
    user = playlist_dict['user']
    pop_movie = playlist_dict['pop_movie']
    pop_tv = playlist_dict['pop_tv']
    
    try:
        for playlist in server.playlists():
            if jbop == 'historyToday':
                if playlist.title.startswith('Aired Today'):
                    playlist.delete()
                    print("...Deleted {playlist.title} for '{user}'."
                          .format(playlist=playlist, user=user))
            elif jbop == 'historyWeek':
                if playlist.title.startswith('Aired This Week'):
                    playlist.delete()
                    print("...Deleted {playlist.title} for '{user}'."
                          .format(playlist=playlist, user=user))
            elif jbop == 'historyMonth':
                if playlist.title.startswith('Aired in'):
                    playlist.delete()
                    print("...Deleted {playlist.title} for '{user}'."
                          .format(playlist=playlist, user=user))
            elif jbop == 'popularMovies':
                if playlist.title == pop_movie:
                    playlist.delete()
                    print("...Deleted {playlist.title} for '{user}'."
                          .format(playlist=playlist, user=user))
            elif jbop == 'popularTv':
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
    parser.add_argument('--libraries', nargs='+', choices=section_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are:\n'
                             'Choices: %(choices)s')
    parser.add_argument('--self', default=False, action='store_true',
                        help='Create playlist for admin.\n'
                             'Default: %(default)s')
    parser.add_argument('--days', type=str, default=DAYS,
                        help='The time range to calculate statistics.\n'
                             'Default: %(default)s')
    parser.add_argument('--top', type=str, default=TOP,
                        help='The number of top items to list.\n'
                             'Default: %(default)s')
    parser.add_argument('--playlists', nargs='+', choices=playlist_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are:\n'
                             'Choices: %(choices)s')
    parser.add_argument('--name', type=str,
                        help='Custom name for playlist.')
    parser.add_argument('--limit', type=int, default=False,
                        help='Limit the amount items to be added to a playlist.')
    # todo-me custom naming for playlists --name?
    # todo-me custom limits to playlist --limit?
    parser.add_argument('--search', action='append', type=lambda kv: kv.split("="),
                        help='Search filter for finding keywords in title, summary or '
                             'filter types (genre, actors, director, studio, etc.')
    
    opts = parser.parse_args()

    users = ''
    search = ''
    plex_servers = []
    pop_movie_title = selectors()['popularMovies'].format(days=opts.days)
    pop_tv_title = selectors()['popularTv'].format(days=opts.days)
    
    playlist_dict = {'jbop': opts.jbop,
                     'custom': opts.name,
                     'pop_tv': pop_tv_title,
                     'pop_movie': pop_movie_title,
                     'limit': opts.limit}
    if opts.search:
        search = dict(opts.search)

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
    
    # Create user server objects
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
        keys_list, title = build_playlist(opts.jbop, opts.libraries, opts.days, opts.top, search)
        
    if opts.jbop and opts.action == 'show':
        show_playlist(title.title(), keys_list)

    if opts.action == 'update':
        print("Deleting the playlist(s)...")
        for x in plex_servers:
            playlist_dict['server'] = x['server']
            playlist_dict['user'] = x['user']
            delete_playlist(playlist_dict)
        print('Creating playlist(s)...')
        for x in plex_servers:
            create_playlist(title.title(), keys_list, x['server'], x['user'])
            
    if opts.action == 'add':
        print('Creating playlist(s)...')
        for x in plex_servers:
            create_playlist(title.title(), keys_list, x['server'], x['user'])

    if opts.action == 'show':
        print("Displaying the user's playlist(s)...")
        for x in plex_servers:
            user = x['user']
            playlist = [y.title for y in x['server'].playlists()]
            print("{}'s current playlist(s): {}".format(user, ', '.join(playlist)))

    print("Done.")
