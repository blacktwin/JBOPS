#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description: Manage Plex media.
             Show, delete, archive, optimize, or move media based on whether it was
             watched, unwatched, transcoded often, or file size is greater than X
             
                    *Tautulli data to command Plex

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
import re
from collections import Counter
from plexapi.server import PlexServer
from plexapi.server import CONFIG
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

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

SELECTOR = ['watched', 'unwatched', 'transcoded', 'rating', 'size']
ACTIONS = ['delete', 'move', 'archive', 'optimize', 'show']
OPERATORS = { '>': lambda v, q: v > q,
              '>=': lambda v, q: v >= q,
              '<': lambda v, q: v < q,
              '<=': lambda v, q: v <= q,}

UNTIS = {"B": 1, "KB": 2**10, "MB": 2**20, "GB": 2**30, "TB": 2**40}

MOVE_PATH = ''
ARCHIVE_PATH = ''
OPTIMIZE_DEFAULT = {'targetTagID': 'Mobile',
                   'deviceProfile': None,
                   'title': None,
                   'target': "",
                   'locationID': -1,
                   'policyUnwatched': 0,
                   'videoQuality': None}

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
        self.type = d['section_type']


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
            # todo only using the first library location for show types
            self.file = show.locations[0]
            show = tautulli_server.get_new_rating_keys(self.rating_key, self.media_type)
            seasons = show['0']['children']
            episodes = []
            show_size = []
            for season in seasons.values():
                for _episode in season['children'].values():
                    metadata = tautulli_server.get_metadata(_episode['rating_key'])
                    episode = Metadata(metadata)
                    show_size.append(int(episode.file_size))
                    episodes.append(episode)
            self.file_size = sum(show_size)
            self.episodes = episodes


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

    def get_history(self, user=None, section_id=None, rating_key=None, start=None, length=None, watched=None,
                    transcode_decision=None):
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
        if transcode_decision:
            payload["transcode_decision"] = transcode_decision

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

    def get_library_media_info(self, section_id, start, length, unwatched=None, date=None, order_column=None):
        """Call Tautulli's get_library_media_info api endpoint."""
        payload = {'section_id': section_id}
        if start:
            payload["start"] = start
        if length:
            payload["lengh"] = length
        if order_column:
            payload["order_column"] = order_column
            payload['order_dir'] = 'desc'
            
        library_stats = self._call_api('get_library_media_info', payload)
        if unwatched and not date:
            return [d for d in library_stats['data'] if d['play_count'] is None]
        elif unwatched and date:
            return [d for d in library_stats['data'] if d['play_count'] is None
                    and (float(d['added_at'])) < date]
        else:
            return [d for d in library_stats['data']]
        
    def get_new_rating_keys(self, rating_key, media_type):
        """Call Tautulli's get_new_rating_keys api endpoint."""
        payload = {"rating_key": rating_key, "media_type": media_type}
        return self._call_api('get_new_rating_keys', payload)
        
        
def sizeof_fmt(num, suffix='B'):
    # Function found https://stackoverflow.com/a/1094933
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def parseSize(size):
    size = size.upper()
    if not re.match(r' ', size):
        size = re.sub(r'([KMGT]?B)', r' \1', size)
    number, unit = [string.strip() for string in size.split()]
    return int(float(number)*UNTIS[unit])


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


def size_work(sectionID, operator, value, episodes):
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
    size_lst = []
    while True:
        
        # Getting all watched history for userFrom
        tt_size = tautulli_server.get_library_media_info(section_id=sectionID,
                                                            start=start, length=count,
                                                            order_column="file_size")
        if all([tt_size]):
            start += count
            for item in tt_size:
                _meta = tautulli_server.get_metadata(item['rating_key'])
                metadata = Metadata(_meta)
                try:
                    if episodes:
                        for _episode in metadata.episodes:
                            file_size = int(_episode.file_size)
                            if operator(file_size, value):
                                size_lst.append(_episode)
                    else:
                        file_size = int(metadata.file_size)
                        if operator(file_size, value):
                            size_lst.append(metadata)
                except AttributeError:
                    print("Metadata error found with rating_key: ({})".format(item['rating_key']))
            continue
        elif not all([tt_size]):
            break
        start += count
    return size_lst


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


def transcode_work(sectionID, operator, value):
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
    transcoding_lst = []
    transcoding_count = {}
    
    while True:
        
        # Getting all watched history for userFrom
        tt_history = tautulli_server.get_history(section_id=sectionID, start=start, length=count,
                                                 transcode_decision="transcode")

        if all([tt_history]):
            start += count
            for item in tt_history:
                if transcoding_count.get(item['rating_key']):
                    transcoding_count[item['rating_key']] += 1
                else:
                    transcoding_count[item['rating_key']] = 1
            
            continue
        elif not all([tt_history]):
            break
        start += count
    
    sorted_transcoding = sorted(transcoding_count.items(), key=lambda x: x[1], reverse=True)
    for rating_key, transcode_count in sorted_transcoding:
        if operator(transcode_count, int(value)):
            _meta = tautulli_server.get_metadata(rating_key)
            if _meta:
                metadata = Metadata(_meta)
                metadata.transcode_count = transcode_count
                transcoding_lst.append(metadata)
            else:
                print("Metadata error found with rating_key: ({})".format(rating_key))
            
    
    return transcoding_lst


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
    parser.add_argument('--actionOption', type=lambda kv: kv.split("="), action='append',
                        help='Addtional instructions to use for move, archive, optimize.\n'
                             '--action optimize --actionOption title="Optimized thing"\n'
                             '--action optimize --actionOption targetTagID=Mobile\n'
                             '--action move --actionOption path="D:/my/new/path"')
    parser.add_argument('--selectValue', type=lambda kv: kv.split("_"),
                        help='Operator and Value to use for size, rating or transcoded filtering.\n'
                             '">_5G" ie. items greater than 5 gigabytes.\n'
                             '">_3" ie. items greater than 3 stars.\n'
                             '">_3" ie. items played transcoded more than 3 times.')
    parser.add_argument('--episodes', action='store_true',
                        help='Enable Plex to scan episodes if Show library is selected.')

    opts = parser.parse_args()
    # todo find: watched by list of users[x], unwatched based on time[x], based on size, most transcoded, star rating
    # todo find: all selectors should be able to search by user, library, and/or time
    # todo actions: delete[x], move?, zip and move?, notify, optimize
    # todo deletion toggle and optimize is dependent on plexapi PRs 433 and 426 respectively
    # todo logging and notification
    # todo if optimizing and optimized version already exists, skip

    libraries = []
    all_sections = []
    watched_lst = []
    unwatched_lst = []
    size_lst = []
    user_lst = []
    transcode_lst = []

    if opts.date:
        date = time.mktime(time.strptime(opts.date, "%Y-%m-%d"))
    else:
        date = None

    # Create a Tautulli instance
    tautulli_server = Tautulli(Connection(url=TAUTULLI_URL.rstrip("/"),
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
                
        if opts.action == "show":
            print("The following items were added before {}".format(opts.date))
            sizes = []
            for item in unwatched_lst:
                added_at = datetime.datetime.utcfromtimestamp(float(item.added_at)).strftime("%Y-%m-%d")
                size = int(item.file_size) if item.file_size else ''
                sizes.append(size)
                print(u"\t{} added {}\tSize: {}\n\t\tFile: {}".format(
                    item.title, added_at, sizeof_fmt(size), item.file))
            total_size = sum(sizes)
            print("Total size: {}".format(sizeof_fmt(total_size)))
            
        if opts.action == "delete":
            plex_deletion(unwatched_lst, libraries, opts.toggleDeletion)

    if opts.select == "watched":
        if libraries:
            for user in user_lst:
                print("Finding watched items from user: {}",format(user.name))
                for _library in libraries:
                    print("Checking library: '{}' watch statuses...".format(_library.title))
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
        
        if opts.action == "show":
            print("The following items were watched by {}".format(", ".join([user.name for user in user_lst])))
            for watched in watched_by_all:
                metadata = user_lst[0].watch[watched]
                print(u"    {}".format(metadata.full_title))
        
        if opts.action == "delete":
            plex_deletion(watched_by_all, libraries, opts.toggleDeletion)
    
    if opts.select in ["size", "rating", "transcoded"]:
        if opts.selectValue:
            operator, value = opts.selectValue
            if operator not in OPERATORS.keys():
                print("Operator not found")
                exit()
        else:
            print("No value provided.")
            exit()
        
        op = OPERATORS.get(operator)
        
        if opts.select == "size":
            if value[-2:] in UNTIS.keys():
                size = parseSize(value)
                if libraries:
                    for _library in libraries:
                        print("Checking library: '{}' items {}{} in size...".format(_library.title, operator, value))
                        size_lst += size_work(sectionID=_library.key, operator=op, value=size, episodes=opts.episodes)

                if opts.action == "show":
                    sizes = []
                    for item in size_lst:
                        added_at = datetime.datetime.utcfromtimestamp(float(item.added_at)).strftime("%Y-%m-%d")
                        size = int(item.file_size) if item.file_size else 0
                        sizes.append(size)
                        print(u"\t{} added {}\tSize: {}\n\t\tFile: {}".format(
                            item.title, added_at, sizeof_fmt(size), item.file))
                    total_size = sum(sizes)
                    print("Total size: {}".format(sizeof_fmt(total_size)))
            else:
                print("Size must end with one of these notations: {}".format(", ".join(UNTIS.keys())))
            pass
        elif opts.select == "rating":
            pass
        elif opts.select == "transcoded":
            if libraries:
                for _library in libraries:
                    print("Checking library: '{}' items with {}{} transcodes...".format(
                        _library.title, operator, value))
                    transcoded_lst = transcode_work(sectionID=_library.key, operator=op, value=value)
                    transcode_lst += transcoded_lst

            if opts.action == "show":
                print("{} item(s) have been found.".format(len(transcode_lst)))
                for item in transcode_lst:
                    added_at = datetime.datetime.utcfromtimestamp(float(item.added_at)).strftime("%Y-%m-%d")
                    size = int(item.file_size) if item.file_size else 0
                    file_size = sizeof_fmt(size)
                    print(u"\t{} added {}\tSize: {}\tTransocded: {} time(s)\n\t\tFile: {}".format(
                        item.title, added_at, file_size, item.transcode_count, item.file))