#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pull library and user statistics of last week.

Library stats can display total items in Shows, Seasons, Episodes, Artists, Albums, Tracks, and Movies

User stats display username and hour, minutes, and seconds of view time

Tautulli Settings > Extra Settings >  Check - Calculate Total File Sizes [experimental] ...... wait

"""
from plexapi.server import CONFIG
from datetime import datetime, timedelta, date
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from operator import itemgetter
import time
import json
import argparse


# EDIT THESE SETTINGS #
TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''
TAUTULLI_PUBLIC_URL = '0'

if not TAUTULLI_URL:
    TAUTULLI_URL = CONFIG.data['auth'].get('tautulli_baseurl')
if not TAUTULLI_APIKEY:
    TAUTULLI_APIKEY = CONFIG.data['auth'].get('tautulli_apikey')
if not TAUTULLI_PUBLIC_URL:
    TAUTULLI_PUBLIC_URL = CONFIG.data['auth'].get('tautulli_public_url')
    
VERIFY_SSL = False

if TAUTULLI_PUBLIC_URL != '/':
    # Check to see if there is a public URL set in Tautulli
    TAUTULLI_LINK = TAUTULLI_PUBLIC_URL
else:
    TAUTULLI_LINK = TAUTULLI_URL
    
RICH_TYPE = ['discord', 'slack']

TAUTULLI_ICON = 'https://github.com/Tautulli/Tautulli/raw/master/data/interfaces/default/images/logo-circle.png'

SUBJECT_TEXT = "Tautulli Weekly Server, Library, and User Statistics"

# Notification notifier ID: https://github.com/JonnyWong16/plexpy/blob/master/API.md#notify
NOTIFIER_ID = 12  # The email notification notifier ID for Tautulli

# Remove library element you do not want shown. Logging before exclusion.
# SHOW_STAT = 'Shows: {0}, Episodes: {2}'
# SHOW_STAT = 'Episodes: {2}'
# SHOW_STAT = ''
SHOW_STAT = 'Shows: {0}, Seasons: {1}, Episodes: {2}'
ARTIST_STAT = 'Artists: {0}, Albums: {1}, Songs: {2}'
PHOTO_STAT = 'Folders: {0}, Subfolders: {1}, Photos: {2}'
MOVIE_STAT = 'Movies: {0}'

# Library names you do not want shown. Logging before exclusion.
LIB_IGNORE = ['XXX']

# Customize user stats display
# User: USER1 -> 1 hr 32 min 00 sec
USER_STAT = 'User: {0} -> {1}'

# Usernames you do not want shown. Logging before exclusion.
USER_IGNORE = ['User1']

# Customize time display
# {0:d} hr {1:02d} min {2:02d} sec  -->  1 hr 32 min 00 sec
# {0:d} hr {1:02d} min  -->  1 hr 32 min
# {0:02d} hr {1:02d} min  -->  01 hr 32 min
TIME_DISPLAY = "{0:d} hr {1:02d} min {2:02d} sec"

# Customize BODY to your liking
BODY_TEXT = """\
<html>
  <head></head>
  <body>
    <p>Hi!<br>
    <br>Below are the current server stats.<br>
    <ul>
    {sections_stats}
    </ul>
    <br>Below are the user stats for the week of ({start} - {end})<br>
    <ol>
    {user_stats}
    </ol>
    </p>
  </body>
</html>
"""

# /EDIT THESE SETTINGS #



def utc_now_iso():
    """Get current time in ISO format"""
    utcnow = datetime.utcnow()

    return utcnow.isoformat()


def hex_to_int(value):
    """Convert hex value to integer"""
    try:
        return int(value, 16)
    except (ValueError, TypeError):
        return 0


def sizeof_fmt(num, suffix='B'):
    # Function found https://stackoverflow.com/a/1094933
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def date_split(to_split):
    split_year = int(to_split.split('-')[0])
    split_month = int(to_split.split('-')[1])
    split_day = int(to_split.split('-')[2])
    return [split_year, split_month, split_day]


def add_to_dictval(d, key, val):
    if key not in d:
        d[key] = val
    else:
        d[key] += val


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def get_user_stats(home_stats):
    user_stats_lst = []
    user_stats_dict = {}
    print('Checking users stats.')
    for stats in home_stats:
        if stats['stat_id'] == 'top_users':
            for row in stats['rows']:
                add_to_dictval(user_stats_dict, row['friendly_name'], row['total_duration'])
                
    for user, duration in sorted(user_stats_dict.items(), key=itemgetter(1), reverse=True):
        if user not in USER_IGNORE:
            user_total = timedelta(seconds=duration)
            USER_STATS = USER_STAT.format(user, user_total)
            # Html formatting
            user_stats_lst += ['<li>{}</li>'.format(USER_STATS)]
    
    return user_stats_lst


def get_library_stats(libraries, tautulli):
    section_count = ''
    total_size = 0
    sections_stats_lst = []

    print('Checking library stats.')
    for section in libraries:

        library = tautulli.get_library_media_info(section['section_id'])
        total_size += library['total_file_size']

        if section['section_type'] == 'artist':
            section_count = ARTIST_STAT.format(section['count'], section['parent_count'], section['child_count'])

        elif section['section_type'] == 'show':
            section_count = SHOW_STAT.format(section['count'], section['parent_count'], section['child_count'])

        elif section['section_type'] == 'photo':
            section_count = PHOTO_STAT.format(section['count'], section['parent_count'], section['child_count'])

        elif section['section_type'] == 'movie':
            section_count = MOVIE_STAT.format(section['count'])

        if section['section_name'] not in LIB_IGNORE and section_count:
            # Html formatting
            sections_stats_lst += ['<li>{}: {}</li>'.format(section['section_name'], section_count)]

    # Html formatting. Adding the Capacity to bottom of list.
    sections_stats_lst += ['<li>Capacity: {}</li>'.format(sizeof_fmt(total_size))]

    return sections_stats_lst


class Tautulli:
    def __init__(self, url, apikey, verify_ssl=False, debug=None):
        self.url = url
        self.apikey = apikey
        self.debug = debug

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
            
            
    def get_library_media_info(self, section_id=None, refresh=None):
        """Call Tautulli's get_activity api endpoint"""
        payload = {}
        if refresh:
            for library in self.get_libraries():
                payload['section_id'] = library['section_id']
                payload['refresh'] = 'true'
                print('Refreshing library: {}'.format(library['section_name']))
                self._call_api('get_library_media_info', payload)
            print('Libraries have been refreshed, please wait while library stats are updated.')
            exit()
        else:
            payload['section_id'] = section_id

        return self._call_api('get_library_media_info', payload)
    
    def get_libraries(self):
        """Call Tautulli's get_activity api endpoint"""
        payload = {}
        
        return self._call_api('get_libraries', payload)

    def get_home_stats(self, time_range, stats_type, stats_count):
        """Call Tautulli's get_activity api endpoint"""
        payload = {}
        payload['time_range'] = time_range
        payload['stats_type'] = stats_type
        payload['stats_count'] = stats_count
        
        return self._call_api('get_home_stats', payload)

    def get_history(self, section_id, check_date):
        """Call Tautulli's get_activity api endpoint"""
        payload = {}
        payload['section_id'] = int(section_id)
        payload['start_date'] = check_date
    
        return self._call_api('get_history', payload)

    def notify(self, notifier_id, subject, body):
        """Call Tautulli's notify api endpoint"""
        payload = {'notifier_id': notifier_id,
                   'subject': subject,
                   'body': body}

        return self._call_api('notify', payload)
    
    def _call_api(self, cmd, payload, method='GET'):
        payload['cmd'] = cmd
        payload['apikey'] = self.apikey

        try:
            response = self.session.request(method, self.url + '/api/v2', params=payload)
        except RequestException as e:
            print("Tautulli request failed for cmd '{}'. Invalid Tautulli URL? Error: {}".format(cmd, e))
            return

        try:
            response_json = response.json()
        except ValueError:
            print(
                "Failed to parse json response for Tautulli API cmd '{}': {}"
                .format(cmd, response.content))
            return

        if response_json['response']['result'] == 'success':
            if self.debug:
                print("Successfully called Tautulli API cmd '{}'".format(cmd))
            return response_json['response']['data']
        else:
            error_msg = response_json['response']['message']
            print("Tautulli API cmd '{}' failed: {}".format(cmd, error_msg))
            return


class Notification:
    def __init__(self, notifier_id, subject, body, tautulli, user=None):
        self.notifier_id = notifier_id
        self.subject = subject
        self.body = body

        self.tautulli = tautulli
        if user:
            self.user = user

    def send(self, subject='', body=''):
        """Send to Tautulli notifier.

        Parameters
        ----------
        subject : str
            Subject of the message.
        body : str
            Body of the message.
        """
        subject = subject or self.subject
        body = body or self.body
        self.tautulli.notify(notifier_id=self.notifier_id, subject=subject, body=body)

    def send_discord(self, title, color, poster_url, plex_url, message, footer):
        """Build the Discord message.

        Parameters
        ----------
        title : str
            The title of the message.
        color : int
            The color of the message
        poster_url : str
            The media poster URL.
        plex_url : str
            Plex media URL.
        message : str
            Message sent to the player.
        footer : str
            Footer of the message.
        """
        discord_message = {
            "embeds": [
                {
                    "author": {
                        "icon_url": TAUTULLI_ICON,
                        "name": "Tautulli",
                        "url": TAUTULLI_LINK.rstrip('/')
                    },
                    "color": color,
                    "fields": [
                        {
                            "inline": True,
                            "name": "User",
                            "value": self.user.friendly_name
                        },
                        {
                            "inline": True,
                            "name": "Watched",
                            "value": self.user.stats
                        },
                        {
                            "inline": False,
                            "name": "Message Sent",
                            "value": message
                        }
                    ],
                    "thumbnail": {
                        "url": poster_url
                    },
                    "title": title,
                    "timestamp": utc_now_iso(),
                    "url": plex_url,
                    "footer": {
                        "text": footer
                    }

                }

            ],
        }

        discord_message = json.dumps(discord_message, sort_keys=True,
                                     separators=(',', ': '))
        self.send(body=discord_message)

    def send_slack(self, title, color, poster_url, plex_url, message, footer):
        """Build the Slack message.

        Parameters
        ----------
        title : str
            The title of the message.
        color : int
            The color of the message
        poster_url : str
            The media poster URL.
        plex_url : str
            Plex media URL.
        message : str
            Message sent to the player.
        footer : str
            Footer of the message.
        """
        slack_message = {
            "attachments": [
                {
                    "title": title,
                    "title_link": plex_url,
                    "author_icon": TAUTULLI_ICON,
                    "author_name": "Tautulli",
                    "author_link": TAUTULLI_LINK.rstrip('/'),
                    "color": color,
                    "fields": [
                        {
                            "title": "User",
                            "value": self.user.friendly_name,
                            "short": True
                        },
                        {
                            "title": "Watched",
                            "value": self.user.stats,
                            "short": True
                        },
                        {
                            "title": "Message Sent",
                            "value": message,
                            "short": False
                        }
                    ],
                    "thumb_url": poster_url,
                    "footer": footer,
                    "ts": time.time()
                }

            ],
        }

        slack_message = json.dumps(slack_message, sort_keys=True,
                                   separators=(',', ': '))
        self.send(body=slack_message)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Use Tautulli to pull library and user statistics for date range.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--days', default=7, metavar='', type=int,
                        help='Enter in number of days to go back. \n(default: %(default)s)')
    parser.add_argument('-t', '--top', default=5, metavar='', type=int,
                        help='Enter in number of top users to find. \n(default: %(default)s)')
    parser.add_argument('--refresh', action='store_true',
                        help='Refresh all libraries in Tautulli')

    opts = parser.parse_args()

    tautulli_server = Tautulli(TAUTULLI_URL.rstrip('/'), TAUTULLI_APIKEY, VERIFY_SSL)
    
    if opts.refresh:
        tautulli_server.get_library_media_info(refresh=True)

    TODAY = int(time.time())
    DAYS = opts.days
    DAYS_AGO = int(TODAY - DAYS * 24 * 60 * 60)
    START_DATE = (datetime.utcfromtimestamp(DAYS_AGO).strftime("%Y-%m-%d"))  # DAYS_AGO as YYYY-MM-DD
    END_DATE = (datetime.utcfromtimestamp(TODAY).strftime("%Y-%m-%d"))  # TODAY as YYYY-MM-DD

    start_date = date(date_split(START_DATE)[0], date_split(START_DATE)[1], date_split(START_DATE)[2])
    end_date = date(date_split(END_DATE)[0], date_split(END_DATE)[1], date_split(END_DATE)[2])

    dates_range_lst = []
    for single_date in daterange(start_date, end_date):
        dates_range_lst += [single_date.strftime("%Y-%m-%d")]

    libraries = tautulli_server.get_libraries()
    lib_stats = get_library_stats(libraries, tautulli_server)
    sections_stats = "\n".join(lib_stats)

    print('Checking user stats from {:02d} days ago.'.format(opts.days))
    home_stats = tautulli_server.get_home_stats(opts.days, 'duration', opts.top)
    user_stats_lst = get_user_stats(home_stats)
    user_stats = "\n".join(user_stats_lst)

    end = datetime.strptime(time.ctime(float(TODAY)), "%a %b %d %H:%M:%S %Y").strftime("%a %b %d %Y")
    start = datetime.strptime(time.ctime(float(DAYS_AGO)), "%a %b %d %H:%M:%S %Y").strftime("%a %b %d %Y")

    BODY_TEXT = BODY_TEXT.format(end=end, start=start, sections_stats=sections_stats, user_stats=user_stats)

    print('Sending message.')
    notify = Notification(NOTIFIER_ID, SUBJECT_TEXT, BODY_TEXT, tautulli_server)
    notify.send()
