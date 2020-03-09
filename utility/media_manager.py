#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description: Manage Plex media.
             Show, delete, archive, optimize, or move media based on whether it was
             watched, unwatched, transcoded often, or file size is greater than X

Author: Blacktwin
Requires: requests, plexapi, argparse
Interacts with: Tautulli, Plex

Enabling Scripts in Tautulli:
 Not yet

 Examples:
     Find unwatched Movies that were added before 2015-05-05 and delete
        python media_manager.py --libraries Movies --select unwatched --date "2015-05-05" --action delete
     
     Find watched TV Shows that both User1 and User2 have watched
        python media_manager.py --libraries "TV Shows" --select watched --users User1 User2

"""
import argparse
import datetime
import time
from collections import Counter
from plexapi.server import PlexServer
from plexapi.server import CONFIG
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

# Using CONFIG file
PLEX_URL =''
PLEX_TOKEN = ''
TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''

if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token')
if not PLEX_URL:
    PLEX_URL = CONFIG.data['auth'].get('server_baseurl')
if not TAUTULLI_URL:
    TAUTULLI_URL = CONFIG.data['auth'].get('tautulli_baseurl')
if not TAUTULLI_APIKEY:
    TAUTULLI_APIKEY = CONFIG.data['auth'].get('tautulli_apikey')

VERIFY_SSL = False

SELECTOR = ['watched', 'unwatched', 'size', 'transcoded']
ACTIONS = ['delete', 'move', 'archive', 'optimize', 'show']


class Connection:
    def __init__(self, url=None, apikey=None, verify_ssl=False):
        self.url = url
        self.apikey = apikey
        self.session = Session()
        self.adapters = HTTPAdapter(max_retries=3,
                                    pool_connections=1,
                                    pool_maxsize=1,
                                    pool_block=True)
        self.session.mount('http://', self.adapters)
        self.session.mount('https://', self.adapters)

        # Ignore verifying the SSL certificate
        if verify_ssl is False:
            self.session.verify = False
            # Disable the warning that the request is insecure, we know that...
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Library(object):
    def __init__(self, data=None):
        d = data or {}
        self.title = d['section_name']
        self.key = d['section_id']


class Metadata(object):
    def __init__(self, data=None):
        d = data or {}
        self.added_at = d.get('added_at')
        self.media_type = d.get('media_type')
        self.grandparent_title = d.get('grandparent_title')
        self.grandparent_rating_key = d.get('grandparent_rating_key')
        self.parent_media_index = d.get('parent_media_index')
        self.parent_title = d.get('parent_title')
        self.parent_rating_key = d.get('parent_rating_key')
        self.file_size = d.get('file_size')
        self.container = d.get('container')
        self.rating_key = d.get('rating_key')
        self.index = d.get('media_index')
        self.watched_status = d.get('watched_status')
        self.libraryName = d.get("library_name")
        self.full_title = d.get('full_title')
        self.title = d.get('title')
        self.year = d.get('year')
        self.video_resolution = d.get('video_resolution')
        self.video_codec = d.get('video_codec')
        self.media_info = d.get('media_info')
        if self.media_info:
            self.parts = self.media_info[0].get('parts')
            self.file = self.parts[0].get('file')
            if not self.file_size:
                self.file_size = self.parts[0].get('file_size')
        if self.media_type == 'episode' and not self.title:
            episodeName = self.full_title.partition('-')[-1]
            self.title = episodeName.lstrip()
        elif not self.title:
            self.title = self.full_title
        
        if self.media_type == 'show':
            show = plex.fetchItem(int(self.rating_key))
            self.file = show.locations[0]
            show_size = []
            episodes = show.episodes()
            for episode in episodes:
                show_size.append(episode.media[0].parts[0].size)
            self.file_size = sum(show_size)


class User(object):
    def __init__(self, name='', email='', userid='',):
        self.name = name
        self.email = email
        self.userid = userid
        self.watch = {}
        self.transcode = {}
        self.direct = {}


class Tautulli:
    def __init__(self, connection):
        self.connection = connection

    def _call_api(self, cmd, payload, method='GET'):
        payload['cmd'] = cmd
        payload['apikey'] = self.connection.apikey

        try:
            response = self.connection.session.request(method, self.connection.url + '/api/v2', params=payload)
        except RequestException as e:
            print("Tautulli request failed for cmd '{}'. Invalid Tautulli URL? Error: {}".format(cmd, e))
            return

        try:
            response_json = response.json()
        except ValueError:
            print("Failed to parse json response for Tautulli API cmd '{}'".format(cmd))
            return

        if response_json['response']['result'] == 'success':
            return response_json['response']['data']
        else:
            error_msg = response_json['response']['message']
            print("Tautulli API cmd '{}' failed: {}".format(cmd, error_msg))
            return

    def get_history(self, user=None, section_id=None, rating_key=None, start=None, length=None, watched=None):
        """Call Tautulli's get_history api endpoint."""
        payload = {"order_column": "full_title",
                   "order_dir": "asc"}
        
        watched_status = None
        if watched is True:
            watched_status = 1
        if watched is False:
            watched_status = 0
        
        if user:
            payload["user"] = user
        if section_id:
            payload["section_id"] = section_id
        if rating_key:
            payload["rating_key"] = rating_key
        if start:
            payload["start"] = start
        if length:
            payload["lengh"] = length

        history = self._call_api('get_history', payload)
        
        if isinstance(watched_status, int):
            return [d for d in history['data'] if d['watched_status'] == watched_status]
        else:
            return [d for d in history['data']]

    def get_metadata(self, rating_key):
        """Call Tautulli's get_metadata api endpoint."""
        payload = {"rating_key": rating_key}
        return self._call_api('get_metadata', payload)

    def get_libraries(self):
        """Call Tautulli's get_libraries api endpoint."""
        payload = {}
        return self._call_api('get_libraries', payload)

    def get_library_media_info(self, section_id, start, length, unwatched=None, date=None):
        """Call Tautulli's get_library_media_info api endpoint."""
        payload = {'section_id': section_id}
        if start:
            payload["start"] = start
        if length:
            payload["lengh"] = length
            
        library_stats = self._call_api('get_library_media_info', payload)
        if unwatched and not date:
            return [d for d in library_stats['data'] if d['play_count'] is None]
        elif unwatched and date:
            return [d for d in library_stats['data'] if d['play_count'] is None
                    and (float(d['added_at'])) < date]


def sizeof_fmt(num, suffix='B'):
    # Function found https://stackoverflow.com/a/1094933
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def plex_deletion(items, libraries, toggleDeletion):
    """
    Parameters
    ----------
    items (list): List of items to be deleted by Plex
    libraries {list): List of libraries used
    toggleDeletion (bool): Allow then disable Plex ability to delete media items

    Returns
    -------

    """
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    if plex.allowMediaDeletion is None and toggleDeletion is None:
        print("Allow Plex to delete media.")
        exit()
    elif plex.allowMediaDeletion is None and toggleDeletion:
        print("Temporarily allowing Plex to delete media.")
        plex._allowMediaDeletion(True)
        time.sleep(1)
        plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    
    print("The following items were added before {} and marked for deletion.".format(opts.date))
    for item in items:
        plex_item = plex.fetchItem(int(item.rating_key))
        plex_item.delete()
        print("Item: {} was deleted".format(item.title))
    for _library in libraries:
        section = plex.library.sectionByID(_library.key)
        print("Emptying Trash from library {}".format(_library.title))
        section.emptyTrash()
    if toggleDeletion:
        print("Disabling Plex to delete media.")
        plex._allowMediaDeletion(False)


def unwatched_work(sectionID, date=None):
    """
    Parameters
    ----------
    sectionID (int): Library key
    date (float): Epoch time

    Returns
    -------
    unwatched_lst (list): List of Metdata objects of unwatched items
    """
    count = 25
    start = 0
    unwatched_lst = []
    while True:
    
        # Getting all watched history for userFrom
        tt_history = tautulli_server.get_library_media_info(section_id=sectionID,
                                                     start=start, length=count, unwatched=True, date=date)
    
        if all([tt_history]):
            start += count
            for item in tt_history:
                _meta = tautulli_server.get_metadata(item['rating_key'])
                metadata = Metadata(_meta)
                unwatched_lst.append(metadata)
            continue
        elif not all([tt_history]):
            break
        start += count

    return unwatched_lst


def watched_work(user, sectionID=None, ratingKey=None):
    """
    Parameters
    ----------
    user (object): User object holding user stats
    sectionID {int): Library key
    ratingKey (int): Item rating key

    -------
    """
    count = 25
    start = 0
    tt_history = ''

    while True:
        
        # Getting all watched history for userFrom
        if sectionID:
            tt_history = tautulli_server.get_history(user=user.name, section_id=sectionID,
                                                             start=start, length=count, watched=True)
        elif ratingKey:
            tt_history = tautulli_server.get_history(user=user.name, rating_key=ratingKey,
                                                             start=start, length=count, watched=True)
        
        if all([tt_history]):
            start += count
            for item in tt_history:
                metadata = Metadata(item)
                if user.watch.get(metadata.rating_key):
                    user.watch.get(metadata.rating_key).watched_status += 1
                else:
                    user.watch.update({metadata.rating_key: metadata})
                    
            continue
        elif not all([tt_history]):
            break
        start += count


if __name__ == '__main__':
    
    session = Connection().session
    plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=session)
    users = {user.title: User(name=user.title, email=user.email, userid=user.id)
             for user in plex.myPlexAccount().users()}
    user_choices = []
    for user in users.values():
        if user.email:
            user_choices.append(user.email)
        user_choices.append(user.userid)
        user_choices.append(user.name)
    sections_lst = [x.title for x in plex.library.sections()]
    
    parser = argparse.ArgumentParser(description="Manage Plex media using data captured from Tautulli.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--select', required=True, choices=SELECTOR,
                        help='Select what kind of items to look for.\nChoices: (%(choices)s)')
    parser.add_argument('--action', required=True, choices=ACTIONS,
                        help='Action to perform with items collected.\nChoices: (%(choices)s)')
    parser.add_argument('--libraries', nargs='+', choices=sections_lst, metavar='',
                        help='Libraries to scan for watched/unwatched content.')
    parser.add_argument('--ratingKey', nargs="?", type=str,
                        help='Rating key of item to scan for watched/unwatched status.')
    parser.add_argument('--date', nargs="?", type=str, default=None,
                        help='Check items added before YYYY-MM-DD for watched/unwatched status.')
    parser.add_argument('--users', nargs='+', choices=user_choices, metavar='',
                        help='Plex usernames, userid, or email of users to use. Allowed names are:\n'
                             'Choices: %(choices)s')
    parser.add_argument('--notify', type=int,
                        help='Notification Agent ID number to Agent to ' +
                        'send notification.')
    parser.add_argument('--toggleDeletion', action='store_true',
                        help='Enable Plex to delete media while using script.')

    opts = parser.parse_args()
    # todo find: watched by list of users[x], unwatched based on time[x], based on size, most transcoded
    # todo actions: delete[x], move?, zip and move?, notify, optimize
    # todo deletion toggle and optimize is dependent on plexapi PRs 433 and 426 respectively
    # todo logging and notification

    libraries = []
    all_sections = []
    watched_lst = []
    unwatched_lst = []
    user_lst = []

    if opts.date:
        date = time.mktime(time.strptime(opts.date, '%Y-%m-%d'))
    else:
        date = None

    # Create a Tautulli instance
    tautulli_server = Tautulli(Connection(url=TAUTULLI_URL.rstrip('/'),
                                          apikey=TAUTULLI_APIKEY,
                                          verify_ssl=VERIFY_SSL))

    # Pull all libraries from Tautulli
    _sections = {}
    tautulli_sections = tautulli_server.get_libraries()
    for section in tautulli_sections:
        section_obj = Library(section)
        _sections[section_obj.title] = section_obj
    all_sections = _sections

    # Defining libraries
    if opts.libraries:
        for library in opts.libraries:
            if all_sections.get(library):
                libraries.append(all_sections.get(library))
            else:
                print("No matching library name '{}'".format(library))
                exit()

    if opts.users:
        for _user in opts.users:
            user_lst.append(users[_user])

    if opts.select == "unwatched":
        if libraries:
            for _library in libraries:
                print("Checking library: '{}' watch statuses...".format(_library.title))
                unwatched_lst += unwatched_work(sectionID=_library.key, date=date)
                
        if opts.action == 'show':
            print("The following items were added before {}".format(opts.date))
            sizes = []
            for item in unwatched_lst:
                added_at = datetime.datetime.utcfromtimestamp(float(item.added_at)).strftime("%Y-%m-%d")
                size = int(item.file_size) if item.file_size else ''
                sizes.append(size)
                print(u"\t{} added {}\tSize: {}\n\t\tFile: {}".format(
                    item.title, added_at, sizeof_fmt(size), item.file))
            total_size = sum(sizes)
            print('Total size: {}'.format(sizeof_fmt(total_size)))
                
        if opts.action == 'delete':
            plex_deletion(unwatched_lst, libraries, opts.toggleDeletion)

    if opts.select == "watched":
        if libraries:
            print("Finding watched items in libraries...")
            for user in user_lst:
                for _library in libraries:
                    print("Checking {}'s library: '{}' watch statuses...".format(user.name, _library.title))
                    watched_work(user=user, sectionID=_library.key)
    
        if opts.ratingKey:
            item = tautulli_server.get_metadata(rating_key=opts.ratingKey)
            metadata = Metadata(item)
            if metadata.media_type in ['show', 'season']:
                parent = plex.fetchItem(int(opts.ratingKey))
                childern = parent.episodes()
                for user in user_lst:
                    for child in childern:
                        watched_work(user=user, ratingKey=child.ratingKey)
            else:
                for user in user_lst:
                    watched_work(user=user, ratingKey=opts.ratingKey)

        # Find all items watched by all users
        all_watched = [key for user in user_lst for key in user.watch.keys()]
        counts = Counter(all_watched)
        watched_by_all = [id for id in all_watched if counts[id] >= len(user_lst)]
        watched_by_all = list(set(watched_by_all))
        
        if opts.action == 'show':
            print("The following items were watched by {}".format(", ".join([user.name for user in user_lst])))
            for watched in watched_by_all:
                metadata = user_lst[0].watch[watched]
                print(u"    {}".format(metadata.full_title))
