"""
Pull library and user statistics of last week.

Library stats can display total items in Shows, Seasons, Episodes, Artists, Albums, Tracks, and Movies

User stats display username and hour, minutes, and seconds of view time

PlexPy Settings > Extra Settings >  Check - Calculate Total File Sizes [experimental] ...... wait

Usage: 
    Use PlexPy to pull library and user statistics for date range.

    optional arguments:
      -h, --help    show this help message and exit
      -d , --days   Enter in number of days to go back.
                    (default: 7)

"""

import requests
import sys
import time
import datetime
import json
from operator import itemgetter
import argparse


# EDIT THESE SETTINGS #
PLEXPY_APIKEY = 'xxxxxx'  # Your PlexPy API key
PLEXPY_URL = 'http://localhost:8181/'  # Your PlexPy URL
SUBJECT_TEXT = "PlexPy Weekly Server, Library, and User Statistics"

# Notification agent ID: https://github.com/JonnyWong16/plexpy/blob/master/API.md#notify
AGENT_ID = 10  # The email notification agent ID for PlexPy

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
    <br>Below are the server stats for the week of ({start} - {end})<br>
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

def get_get_history(user_id, check_date):
    # Get the PlexPy history.
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_history',
               'user_id': user_id,
               'start_date': check_date}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        # print(json.dumps(response['response']['data'], indent=4, sort_keys=True))
        res_data = response['response']['data']
        return res_data

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_history' request failed: {0}.".format(e))


def get_get_user_names():
    # Get a list of all user and user ids.
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_user_names'}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']
        return [d for d in res_data if d['friendly_name'] != 'Local']

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_user_names' request failed: {0}.".format(e))


def get_get_libraries():
    # Get a list of all libraries on your server.
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_libraries'}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        # print(json.dumps(response['response']['data'], indent=4, sort_keys=True))
        res_data = response['response']['data']
        return res_data

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_libraries' request failed: {0}.".format(e))


def get_get_library_media_info(section_id):
    # Get a list of all libraries on your server.
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_library_media_info',
               'section_id': section_id,
               'refresh': True}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        # print(json.dumps(response['response']['data'], indent=4, sort_keys=True))
        res_data = response['response']['data']
        return res_data['total_file_size']

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_library_media_info' request failed: {0}.".format(e))


def send_notification(body_text):
    # Format notification text
    try:
        subject = SUBJECT_TEXT
        body = body_text
    except LookupError as e:
        sys.stderr.write("Unable to substitute '{0}' in the notification subject or body".format(e))
        return None
    # Send the notification through PlexPy
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'notify',
               'agent_id': AGENT_ID,
               'subject': subject,
               'body': body}

    try:
        r = requests.post(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        if response['response']['result'] == 'success':
            sys.stdout.write("Successfully sent PlexPy notification.")
        else:
            raise Exception(response['response']['message'])
    except Exception as e:
        sys.stderr.write("PlexPy API 'notify' request failed: {0}.".format(e))
        return None


def sizeof_fmt(num, suffix='B'):
    # Function found https://stackoverflow.com/a/1094933
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def add_to_dictlist(d, key, val):
    if key not in d:
        d[key] = val
    else:
        d[key] += val


def get_user_stats(dates_range_lst):

    user_stats_dict = {}
    user_stats_lst = []

    for check_date in dates_range_lst:
        print('Checking user stats for date: {}'.format(check_date))

        for users in get_get_user_names():
            history = get_get_history(users['user_id'], check_date)
            if history['filter_duration'] != '0':
                user_name = users['friendly_name']
                user_totals = sum([d['duration'] for d in history['data']])
                add_to_dictlist(user_stats_dict, user_name, user_totals)

    # print(user_stats_dict)

    for user, duration in sorted(user_stats_dict.items(), key=itemgetter(1), reverse=True):
        if user not in USER_IGNORE:
            m, s = divmod(duration, 60)
            h, m = divmod(m, 60)
            easy_time = TIME_DISPLAY.format(h, m, s)
            USER_STATS = USER_STAT.format(user, easy_time)
            # Html formatting
            user_stats_lst += ['<li>{}</li>'.format(USER_STATS)]
        else:
            pass

    # print(user_stats_lst)
    return user_stats_lst


def get_sections_stats():
    section_count = ''
    total_size = 0
    sections_stats_lst = []

    for sections in get_get_libraries():

        lib_size = get_get_library_media_info(sections['section_id'])
        total_size += lib_size

        if sections['section_type'] == 'artist':
            section_count = ARTIST_STAT.format(sections['count'], sections['parent_count'], sections['child_count'])

        elif sections['section_type'] == 'show':
            section_count = SHOW_STAT.format(sections['count'], sections['parent_count'], sections['child_count'])

        elif sections['section_type'] == 'photo':
            section_count = PHOTO_STAT.format(sections['count'], sections['parent_count'], sections['child_count'])

        elif sections['section_type'] == 'movie':
            section_count = MOVIE_STAT.format(sections['count'])

        else:
            pass

        if sections['section_name'] not in LIB_IGNORE and section_count:
            # Html formatting
            sections_stats_lst += ['<li>{}: {}</li>'.format(sections['section_name'], section_count)]

    # Html formatting. Adding the Capacity to bottom of list.
    sections_stats_lst += ['<li>Capacity: {}</li>'.format(sizeof_fmt(total_size))]

    # print(sections_stats_lst)
    return sections_stats_lst


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + datetime.timedelta(n)


def date_split(to_split):
    split_year = int(to_split.split('-')[0])
    split_month = int(to_split.split('-')[1])
    split_day = int(to_split.split('-')[2])
    return [split_year, split_month, split_day]


def main():

    global BODY_TEXT

    parser = argparse.ArgumentParser(description="Use PlexPy to pull library and user statistics for date range.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--days', default=3, metavar='', type=int,
                        help='Enter in number of days to go back. \n(default: %(default)s)')

    opts = parser.parse_args()

    TODAY = int(time.time())
    DAYS = opts.days
    DAYS_AGO = int(TODAY - DAYS * 24 * 60 * 60)
    START_DATE = (datetime.datetime.utcfromtimestamp(DAYS_AGO).strftime("%Y-%m-%d"))  # DAYS_AGO as YYYY-MM-DD
    END_DATE = (datetime.datetime.utcfromtimestamp(TODAY).strftime("%Y-%m-%d"))  # TODAY as YYYY-MM-DD

    start_date = datetime.date(date_split(START_DATE)[0], date_split(START_DATE)[1], date_split(START_DATE)[2])
    end_date = datetime.date(date_split(END_DATE)[0], date_split(END_DATE)[1], date_split(END_DATE)[2])
    
    dates_range_lst = []
    
    for single_date in daterange(start_date, end_date):
        dates_range_lst += [single_date.strftime("%Y-%m-%d")]

    print('Checking users stats from {:02d} days ago.'.format(opts.days))
    user_stats_lst = get_user_stats(dates_range_lst)
    # print(user_stats_lst)

    print('Checking library stats.')
    lib_stats = get_sections_stats()
    # print(lib_stats)

    end = datetime.datetime.strptime(time.ctime(float(TODAY)), "%a %b %d %H:%M:%S %Y").strftime("%a %b %d %Y")
    start = datetime.datetime.strptime(time.ctime(float(DAYS_AGO)), "%a %b %d %H:%M:%S %Y").strftime("%a %b %d %Y")

    sections_stats = "\n".join(lib_stats)
    user_stats = "\n".join(user_stats_lst)

    BODY_TEXT = BODY_TEXT.format(end=end, start=start, sections_stats=sections_stats, user_stats=user_stats)

    send_notification(BODY_TEXT)

if __name__ == '__main__':
    main()
