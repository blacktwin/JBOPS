#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
        self.count = d['count']
        self.type = d['section_type']
        try:
            self.parent_count = d['parent_count']
            self.child_count = d['child_count']
        except Exception:
            # print(e)
            pass


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


class Plex:
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


def make_pie(user_dict, sections_dict, title, filename=None, headless=None):

    import matplotlib as mpl
    mpl.rcParams['text.color'] = FONT_COLOR
    mpl.rcParams['axes.labelcolor'] = FONT_COLOR
    mpl.rcParams['xtick.color'] = FONT_COLOR
    mpl.rcParams['ytick.color'] = FONT_COLOR
    if headless:
        mpl.use("Agg")

    import matplotlib.pyplot as plt
    user_len = len(user_dict.keys())
    section_len = len(sections_dict.keys())
    user_position = 0

    fig = plt.figure(figsize=(section_len + 6, user_len + 6), facecolor=BACKGROUND_COLOR)

    for user, values in user_dict.items():
        section_position = 0
        for library, watched_value in values.items():
            library_total = sections_dict.get(library)
            fracs = [watched_value, library_total]
            ax = plt.subplot2grid((user_len, section_len), (user_position, section_position))
            ax.pie(fracs, explode=EXPLODE, colors=COLORS, pctdistance=1.3,
                   autopct='%1.1f%%', shadow=True, startangle=300, radius=0.8,
                   wedgeprops=dict(width=0.5, edgecolor=BACKGROUND_COLOR))

            if user_position == 0:
                ax.set_title("{}: {}".format(library, library_total), bbox=BBOX_PROPS,
                             ha='center', va='bottom', size=12)
            if section_position == 0:
                ax.set_ylabel(user, bbox=BBOX_PROPS, size=13).set_rotation(0)
                ax.yaxis.labelpad = 40
            ax.set_xlabel("User watched: {}".format(watched_value), bbox=BBOX_PROPS)
            section_position += 1
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
    parser.add_argument('--users', nargs='*', metavar='users',
                        help='Users to scan for watched content.')
    parser.add_argument('--pie', default=False, action='store_true',
                        help='Display pie chart')
    parser.add_argument('--filename', type=str, default='Users_Watched_{}'.format(timestr), metavar='',
                        help='Filename of pie chart. None will not save. \n(default: %(default)s)')
    parser.add_argument('--headless', action='store_true', help='Run headless.')

    opts = parser.parse_args()

    sections_totals_dict = {}
    sections_dict = {}
    user_dict = {}
    title = "User's Watch Percentage by Library\nFrom: {}"

    if opts.plex:
        admin_account = Plex(PLEX_TOKEN)
        plex_server = Plex(PLEX_TOKEN, PLEX_URL)
        title = title.format(plex_server.server.friendlyName)

        for library in opts.libraries:
            section_total = plex_server.all_sections_totals(library)
            sections_totals_dict[library] = section_total
            print("Section: {}, has {} items.".format(library, section_total))
            for user in opts.users:
                try:
                    user_account = admin_account.account.user(user)
                    token = user_account.get_token(plex_server.server.machineIdentifier)
                    user_server = Plex(url=PLEX_URL, token=token)
                    section = user_server.server.library.section(library)
                    if section.type == 'movie':
                        section_watched_lst = section.search(unwatched=False)
                    elif section.type == 'show':
                        section_watched_lst = section.search(libtype='episode', unwatched=False)
                    else:
                        continue
                    section_watched_total = len(section_watched_lst)
                    percent_watched = 100 * (float(section_watched_total) / float(section_total))
                    print("    {} has watched {} items ({}%).".format(user, section_watched_total, int(percent_watched)))

                    if user_dict.get(user):
                        user_dict[user].update({library: section_watched_total})
                    else:
                        user_dict[user] = {library: section_watched_total}
                except Exception as e:
                    print(user, e)
                    if user_dict.get(user):
                        user_dict[user].update({library: 0})
                    else:
                        user_dict[user] = {library: 0}

    elif opts.tautulli:
        # Create a Tautulli instance
        tautulli_server = Tautulli(Connection(url=TAUTULLI_URL.rstrip('/'),
                                              apikey=TAUTULLI_APIKEY,
                                              verify_ssl=VERIFY_SSL))
        # Pull all libraries from Tautulli
        tautulli_sections = tautulli_server.get_libraries()
        title = title.format("Tautulli")
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
            sections_totals_dict[library] = section_total
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
                    print(user, e)

                section_watched_total = len(list(set(section_watched_lst)))
                percent_watched = 100 * (float(section_watched_total) / float(section_total))
                print("    {} has watched {} items ({}%).".format(user, section_watched_total, int(percent_watched)))

                if user_dict.get(user):
                    user_dict[user].update({library: section_watched_total})
                else:
                    user_dict[user] = {library: section_watched_total}

    if opts.pie:
        make_pie(user_dict, sections_totals_dict, title, opts.filename, opts.headless)
