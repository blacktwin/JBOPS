#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from builtins import object
import time
import argparse
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from plexapi.server import CONFIG
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

# Using CONFIG file
PLEX_URL = ''
PLEX_TOKEN = ''
TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''

FONT_COLOR = '#FFFFFF'
BACKGROUND_COLOR = '#282828'
BOX_COLOR = '#3C3C3C'
BBOX_PROPS = dict(boxstyle="round,pad=0.7, rounding_size=0.3", fc=BOX_COLOR, ec=BOX_COLOR)

# [user, section] for Explode and Color
EXPLODE = [0, 0.01]
COLORS = ['#F6A821', '#C07D37']

if not PLEX_URL:
    PLEX_URL = CONFIG.data['auth'].get('server_baseurl')
if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token')
if not TAUTULLI_URL:
    TAUTULLI_URL = CONFIG.data['auth'].get('tautulli_baseurl')
if not TAUTULLI_APIKEY:
    TAUTULLI_APIKEY = CONFIG.data['auth'].get('tautulli_apikey')

VERIFY_SSL = False

timestr = time.strftime("%Y%m%d-%H%M%S")


class Connection(object):
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
        self.count = d['count']
        self.type = d['section_type']
        try:
            self.parent_count = d['parent_count']
            self.child_count = d['child_count']
        except Exception:
            # print(e)
            pass


class Tautulli(object):
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

    def get_watched_history(self, user=None, section_id=None, rating_key=None, start=None, length=None):
        """Call Tautulli's get_history api endpoint"""
        payload = {"order_column": "full_title",
                   "order_dir": "asc"}
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

        return [d for d in history['data'] if d['watched_status'] == 1]

    def get_libraries(self):
        """Call Tautulli's get_libraries api endpoint"""

        payload = {}
        return self._call_api('get_libraries', payload)


class Plex(object):
    def __init__(self, token, url=None):
        if token and not url:
            self.account = MyPlexAccount(token)
        if token and url:
            session = Connection().session
            self.server = PlexServer(baseurl=url, token=token, session=session)

    def all_users(self):
        """All users
        Returns
        -------
        data: dict
        """
        users = {self.account.title: self.account}
        for user in self.account.users():
            users[user.title] = user

        return users

    def all_sections(self):
        """All sections from server
        Returns
        -------
        sections: dict
            {section title: section object}
        """
        sections = {section.title: section for section in self.server.library.sections()}

        return sections
    
    def all_collections(self):
        """All collections from server
        Returns
        -------
        collections: dict
            {collection title: collection object}
        """
        collections = {}
        for section in self.all_sections().values():
            if section.type != 'photo':
                for collection in section.collections():
                    collections[collection.title] = collection

        return collections
    
    def all_shows(self):
        """All collections from server
        Returns
        -------
        shows: dict
            {Show title: show object}
        """
        shows = {}
        for section in self.all_sections().values():
            if section.type == 'show':
                for show in section.all():
                    shows[show.title] = show

        return shows

    def all_sections_totals(self, library=None):
        """All sections total items
        Returns
        -------
        section_totals: dict or int
            {section title: section object} or int
        """
        section_totals = {}
        if library:
            sections = [self.all_sections()[library]]
        else:
            sections = self.all_sections()
        for section in sections:
            if section.type == 'movie':
                section_total = len(section.all())
            elif section.type == 'show':
                section_total = len(section.search(libtype='episode'))
            else:
                continue

            if library:
                return section_total

            section_totals[section.title] = section_total

        return section_totals


def make_pie(user_dict, source_dict, title, filename=None, image=None, headless=None):

    import matplotlib as mpl
    mpl.rcParams['text.color'] = FONT_COLOR
    mpl.rcParams['axes.labelcolor'] = FONT_COLOR
    mpl.rcParams['xtick.color'] = FONT_COLOR
    mpl.rcParams['ytick.color'] = FONT_COLOR
    if headless:
        mpl.use("Agg")

    import matplotlib.pyplot as plt
    
    user_len = len(user_dict.keys())
    source_len = len(source_dict.keys())
    user_position = 0
    
    fig = plt.figure(figsize=(source_len + 10, user_len + 10), facecolor=BACKGROUND_COLOR)

    for user, values in user_dict.items():
        source_position = 0
        for source, watched_value in values.items():
            source_total = source_dict.get(source)
            percent_watched = 100 * (float(watched_value) / float(source_total))
            fracs = [percent_watched, 100 - percent_watched]
            ax = plt.subplot2grid((user_len, source_len), (user_position, source_position))
            pie, text, autotext = ax.pie(fracs, explode=EXPLODE, colors=COLORS, pctdistance=1.3,
                   autopct='%1.1f%%', shadow=True, startangle=300, radius=0.8,
                   wedgeprops=dict(width=0.5, edgecolor=BACKGROUND_COLOR))

            if user_position == 0:
                ax.set_title("{}: {}".format(source, source_total), bbox=BBOX_PROPS,
                             ha='center', va='bottom', size=12)
            if source_position == 0:
                ax.set_ylabel(user, bbox=BBOX_PROPS, size=13, horizontalalignment='right').set_rotation(0)
                ax.yaxis.labelpad = 40
            ax.set_xlabel("User watched: {}".format(watched_value), bbox=BBOX_PROPS)
            source_position += 1
        user_position += 1

    plt.suptitle(title, bbox=BBOX_PROPS, size=15)
    plt.tight_layout()
    fig.subplots_adjust(top=0.88)

    if filename:
        plt.savefig('{}_{}.png'.format(filename, timestr), facecolor=BACKGROUND_COLOR)
        print('Image saved as: {}_{}.png'.format(filename, timestr))
    if not headless:
        plt.show()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Show watched percentage of users by libraries.",
                                     formatter_class=argparse.RawTextHelpFormatter)

    servers = parser.add_mutually_exclusive_group()
    servers.add_argument('--plex', default=False, action='store_true',
                         help='Pull data from Plex')
    servers.add_argument('--tautulli', default=False, action='store_true',
                         help='Pull data from Tautulli')

    parser.add_argument('--libraries', nargs='*', metavar='library',
                        help='Libraries to scan for watched content.')
    parser.add_argument('--collections', nargs='*', metavar='collection',
                        help='Collections to scan for watched content.')
    parser.add_argument('--shows', nargs='*', metavar='show',
                        help='Shows to scan for watched content.')
    parser.add_argument('--users', nargs='*', metavar='users',
                        help='Users to scan for watched content.')
    parser.add_argument('--pie', default=False, action='store_true',
                        help='Display pie chart')
    parser.add_argument('--filename', type=str, default='Users_Watched_{}'.format(timestr), metavar='',
                        help='Filename of pie chart. None will not save. \n(default: %(default)s)')
    parser.add_argument('--headless', action='store_true', help='Run headless.')

    opts = parser.parse_args()

    source_dict = {}
    user_servers = []
    sections_dict = {}
    user_dict = {}
    title = ''
    image = ''


    if opts.plex:
        admin_account = Plex(PLEX_TOKEN)
        plex_server = Plex(PLEX_TOKEN, PLEX_URL)
        for user in opts.users:
            user_server = plex_server.server.switchUser(user)
            user_server._username = user
            user_servers.append(user_server)
        
        if opts.libraries:
            title = "User's Watch Percentage by Library\nFrom: {}"
            title = title.format(plex_server.server.friendlyName)

            for library in opts.libraries:
                section_total = plex_server.all_sections_totals(library)
                source_dict[library] = section_total
                print("Section: {}, has {} items.".format(library, section_total))
                for user_server in user_servers:
                    section = user_server.library.section(library)
                    if section.type == 'movie':
                        section_watched_lst = section.search(unwatched=False)
                    elif section.type == 'show':
                        section_watched_lst = section.search(libtype='episode', unwatched=False)
                    else:
                        continue
                    section_watched_total = len(section_watched_lst)
                    percent_watched = 100 * (float(section_watched_total) / float(section_total))
                    print("    {} has watched {} items ({}%).".format(user_server._username, section_watched_total,
                                                                      int(percent_watched)))

                    if user_dict.get(user_server._username):
                        user_dict[user_server._username].update({library: section_watched_total})
                    else:
                        user_dict[user_server._username] = {library: section_watched_total}
                            
        if opts.collections:
            title = "User's Watch Percentage by Collection\nFrom: {}"
            title = title.format(plex_server.server.friendlyName)
            for collection in opts.collections:
                _collection = plex_server.all_collections()[collection]
                collection_albums = _collection.items()
                collection_total = len(collection_albums)
                source_dict[collection] = collection_total
                print("Collection: {}, has {} items.".format(collection, collection_total))
                if _collection.subtype == 'album':
                    for user_server in user_servers:
                        collection_watched_lst = []
                        user_collection = user_server.fetchItem(_collection.ratingKey)
                        for album in user_collection.items():
                            if album.viewedLeafCount:
                                collection_watched_lst.append(album)
                        collection_watched_total = len(collection_watched_lst)
                        percent_watched = 100 * (float(collection_watched_total) / float(collection_total))
                        print("    {} has listened {} items ({}%).".format(user_server._username,
                                                                           collection_watched_total,
                                                                          int(percent_watched)))
                        if user_dict.get(user_server._username):
                            user_dict[user_server._username].update({collection: collection_watched_total})
                        else:
                            user_dict[user_server._username] = {collection: collection_watched_total}
                        
                else:
                    collection_items = _collection.items()
                    collection_total = len(collection_items)
                    thumb_url = '{}{}&X-Plex-Token={}'.format(PLEX_URL, _collection.thumb, PLEX_TOKEN)
                    # image = rget(thumb_url, stream=True)
                    image = urllib.request.urlretrieve(thumb_url)
                    for user_server in user_servers:
                        collection_watched_lst = []
                        for item in collection_items:
                            user_item = user_server.fetchItem(item.ratingKey)
                            if user_item.isWatched:
                                collection_watched_lst.append(user_item)
                        collection_watched_total = len(collection_watched_lst)
                        percent_watched = 100 * (float(collection_watched_total) / float(collection_total))
                        print("    {} has watched {} items ({}%).".format(user_server._username,
                                                                          collection_watched_total,
                                                                          int(percent_watched)))
                        if user_dict.get(user_server._username):
                            user_dict[user_server._username].update({collection: collection_watched_total})
                        else:
                            user_dict[user_server._username] = {collection: collection_watched_total}

        if opts.shows:
            title = "User's Watch Percentage by Shows\nFrom: {}"
            title = title.format(plex_server.server.friendlyName)
            all_shows = plex_server.all_shows()
            
            for show_title in opts.shows:
                show = all_shows.get(show_title)
                episode_total = len(show.episodes())
                season_total = len(show.seasons())
                source_dict[show_title] = len(show.episodes())
                print("Show: {}, has {} episodes.".format(show_title, episode_total))
                for user_server in user_servers:
                    user_show = user_server.fetchItem(show.ratingKey)
                    source_watched_lst = user_show.watched()
                    source_watched_total = len(source_watched_lst)
                    percent_watched = 100 * (float(source_watched_total) / float(episode_total))
                    print("    {} has watched {} items ({}%).".format(user_server._username, source_watched_total,
                                                                      int(percent_watched)))
            
                    if user_dict.get(user_server._username):
                        user_dict[user_server._username].update({show_title: source_watched_total})
                    else:
                        user_dict[user_server._username] = {show_title: source_watched_total}

    elif opts.tautulli:
        # Create a Tautulli instance
        tautulli_server = Tautulli(Connection(url=TAUTULLI_URL.rstrip('/'),
                                              apikey=TAUTULLI_APIKEY,
                                              verify_ssl=VERIFY_SSL))
        # Pull all libraries from Tautulli
        tautulli_sections = tautulli_server.get_libraries()
        title = "User's Watch Percentage by Library\nFrom: Tautulli"
        for section in tautulli_sections:
            library = Library(section)
            sections_dict[library.title] = library

        for library in opts.libraries:
            section = sections_dict[library]
            if section.type == "movie":
                section_total = section.count
            elif section.type == "show":
                section_total = section.child_count
            else:
                print("Not doing that...")
                section_total = 0

            print("Section: {}, has {} items.".format(library, section_total))
            source_dict[library] = section_total
            for user in opts.users:
                count = 25
                start = 0
                section_watched_lst = []
                try:
                    while True:
                        # Getting all watched history for userFrom
                        tt_watched = tautulli_server.get_watched_history(user=user, section_id=section.key,
                                                                         start=start, length=count)
                        if all([tt_watched]):
                            start += count
                            for item in tt_watched:
                                section_watched_lst.append(item["rating_key"])
                            continue
                        elif not all([tt_watched]):
                            break
                        start += count

                except Exception as e:
                    print((user, e))

                section_watched_total = len(list(set(section_watched_lst)))
                percent_watched = 100 * (float(section_watched_total) / float(section_total))
                print("    {} has watched {} items ({}%).".format(user, section_watched_total, int(percent_watched)))

                if user_dict.get(user):
                    user_dict[user].update({library: section_watched_total})
                else:
                    user_dict[user] = {library: section_watched_total}

    if opts.pie:
        make_pie(user_dict, source_dict, title, opts.filename, image, opts.headless)
