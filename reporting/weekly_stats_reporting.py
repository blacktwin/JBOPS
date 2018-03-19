"""
Pull library and user statistics of last week.

Library stats can display total items in Shows, Seasons, Episodes, Artists, Albums, Tracks, and Movies

User stats display username and hour, minutes, and seconds of view time

Tautulli Settings > Extra Settings >  Check - Calculate Total File Sizes [experimental] ...... wait

"""

import requests
import sys
import time
import datetime
import json
from operator import itemgetter
import argparse


# EDIT THESE SETTINGS #
TAUTULLI_APIKEY = 'xxxxx'  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL
SUBJECT_TEXT = "Tautulli Weekly Server, Library, and User Statistics"

# Notification notifier ID: https://github.com/JonnyWong16/plexpy/blob/master/API.md#notify
NOTIFIER_ID = 10  # The email notification notifier ID for Tautulli

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

def get_history(section_id, check_date):
    # Get the Tautulli history.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'section_id': section_id,
               'start_date': check_date}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        # print(json.dumps(response['response']['data'], indent=4, sort_keys=True))
        res_data = response['response']['data']
        if res_data['filter_duration'] != '0':
            return res_data['data']
        else:
            pass

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))


def get_libraries():
    # Get a list of all libraries on your server.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_libraries'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        # print(json.dumps(response['response']['data'], indent=4, sort_keys=True))
        res_data = response['response']['data']
        return res_data

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_libraries' request failed: {0}.".format(e))


def get_library_media_info(section_id):
    # Get a list of all libraries on your server.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_library_media_info',
               'section_id': section_id}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        # print(json.dumps(response['response']['data'], indent=4, sort_keys=True))
        res_data = response['response']['data']
        return res_data['total_file_size']

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_library_media_info' request failed: {0}.".format(e))


def send_notification(body_text):
    # Format notification text
    try:
        subject = SUBJECT_TEXT
        body = body_text
    except LookupError as e:
        sys.stderr.write("Unable to substitute '{0}' in the notification subject or body".format(e))
        return None
    # Send the notification through Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'notify',
               'notifier_id': NOTIFIER_ID,
               'subject': subject,
               'body': body}

    try:
        r = requests.post(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        if response['response']['result'] == 'success':
            sys.stdout.write("Successfully sent Tautulli notification.")
        else:
            raise Exception(response['response']['message'])
    except Exception as e:
        sys.stderr.write("Tautulli API 'notify' request failed: {0}.".format(e))
        return None


def sizeof_fmt(num, suffix='B'):
    # Function found https://stackoverflow.com/a/1094933
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
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
    #print(d, key, val)
    if key not in d:
        d[key] = val
    else:
        d[key] += val


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + datetime.timedelta(n)


def get_server_stats(date_ranges):
    section_count = ''
    total_size = 0
    sections_id_lst = []
    sections_stats_lst = []
    user_stats_lst = []
    user_stats_dict = {}
    user_names_lst = []
    user_durations_lst =[]

    print('Checking library stats.')
    for sections in get_libraries():

        lib_size = get_library_media_info(sections['section_id'])
        total_size += lib_size
        sections_id_lst += [sections['section_id']]

        if sections['section_type'] == 'artist':
            section_count = ARTIST_STAT.format(sections['count'], sections['parent_count'], sections['child_count'])

        elif sections['section_type'] == 'show':
            section_count = SHOW_STAT.format(sections['count'], sections['parent_count'], sections['child_count'])

        elif sections['section_type'] == 'photo':
            section_count = PHOTO_STAT.format(sections['count'], sections['parent_count'], sections['child_count'])

        elif sections['section_type'] == 'movie':
            section_count = MOVIE_STAT.format(sections['count'])

        if sections['section_name'] not in LIB_IGNORE and section_count:
            # Html formatting
            sections_stats_lst += ['<li>{}: {}</li>'.format(sections['section_name'], section_count)]

    print('Checking users stats.')
    # print(sections_id_lst)
    for check_date in date_ranges:
        for section_id in sections_id_lst:
            # print(check_date, section_id)
            history = get_history(section_id, check_date)
            if history:
                # print(json.dumps(history, indent=4, sort_keys=True))
                for data in history:
                    # print(data)
                    user_names_lst += [data['friendly_name']]
                    user_durations_lst += [data['duration']]
                # print(user_durations_lst, user_names_lst)
                for user_name, user_totals in zip(user_names_lst, user_durations_lst):
                    add_to_dictval(user_stats_dict, user_name, user_totals)

        print('{} watched something on {}'.format(' & '.join(set(user_names_lst)), check_date))
    # print(json.dumps(user_stats_dict, indent=4, sort_keys=True))
    for user, duration in sorted(user_stats_dict.items(), key=itemgetter(1), reverse=True):
        if user not in USER_IGNORE:
            m, s = divmod(duration, 60)
            h, m = divmod(m, 60)
            easy_time = TIME_DISPLAY.format(h, m, s)
            USER_STATS = USER_STAT.format(user, easy_time)
            # Html formatting
            user_stats_lst += ['<li>{}</li>'.format(USER_STATS)]

    # Html formatting. Adding the Capacity to bottom of list.
    sections_stats_lst += ['<li>Capacity: {}</li>'.format(sizeof_fmt(total_size))]

    # print(sections_stats_lst, user_stats_lst)
    return (sections_stats_lst, user_stats_lst)


def main():

    global BODY_TEXT

    parser = argparse.ArgumentParser(description="Use Tautulli to pull library and user statistics for date range.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--days', default=7, metavar='', type=int,
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

    print('Checking user stats from {:02d} days ago.'.format(opts.days))

    lib_stats, user_stats_lst = get_server_stats(dates_range_lst)
    # print(lib_stats)

    end = datetime.datetime.strptime(time.ctime(float(TODAY)), "%a %b %d %H:%M:%S %Y").strftime("%a %b %d %Y")
    start = datetime.datetime.strptime(time.ctime(float(DAYS_AGO)), "%a %b %d %H:%M:%S %Y").strftime("%a %b %d %Y")

    sections_stats = "\n".join(lib_stats)
    user_stats = "\n".join(user_stats_lst)

    BODY_TEXT = BODY_TEXT.format(end=end, start=start, sections_stats=sections_stats, user_stats=user_stats)

    print('Sending message.')
    send_notification(BODY_TEXT)

if __name__ == '__main__':
    main()
