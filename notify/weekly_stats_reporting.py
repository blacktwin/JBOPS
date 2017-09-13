"""
Pull library and user statistics of last week.

Library stats can display total items in Shows, Seasons, Episodes, Artists, Albums, Tracks, and Movies

User stats display username and hour, minutes, and seconds of view time

PlexPy Settings > Extra Settings >  Check - Calculate Total File Sizes [experimental] ...... wait

"""

import requests
import sys
import time
import datetime
import json
from operator import itemgetter

TODAY = int(time.time())
LASTWEEK = int(TODAY - 7 * 24 * 60 * 60)
START_DATE = (datetime.datetime.utcfromtimestamp(LASTWEEK).strftime("%Y-%m-%d"))  # LASTWEEK as YYYY-MM-DD
END_DATE = (datetime.datetime.utcfromtimestamp(TODAY).strftime("%Y-%m-%d"))  # TODAY as YYYY-MM-DD

# EDIT THESE SETTINGS #
PLEXPY_APIKEY = 'xxxxxxx'  # Your PlexPy API key
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

def get_get_history(user_id):
    # Get the PlexPy history.
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_history',
               'user_id': user_id,
               'start_date': START_DATE}

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
        # print(json.dumps(response['response']['data'], indent=4, sort_keys=True))
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


def add_to_dictlist(d, key, val):
    if key not in d:
        d[key] = [val]
    else:
        d[key].append(val)


def sizeof_fmt(num, suffix='B'):
    # Function found https://stackoverflow.com/a/1094933
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def get_user_stats(user_stats_lst, stat_logging, user_stats):
    # Pull User stats and
    user_duration = []

    for users in get_get_user_names():
        history = get_get_history(users['user_id'])
        if history['filter_duration'] != '0':
            user_name = users['friendly_name']
            user_totals = sum([d['duration'] for d in history['data']])
            user_duration.append([user_name, user_totals])
            add_to_dictlist(stat_logging['data'], 'data', {'user': user_name, 'duration': user_totals})

    user_duration = sorted(user_duration, key=itemgetter(1), reverse=True)

    for user_stat in user_duration:
        if user_stat[0] not in USER_IGNORE:
            m, s = divmod(user_stat[1], 60)
            h, m = divmod(m, 60)
            easy_time = TIME_DISPLAY.format(h, m, s)
            USER_STAT = user_stats.format(user_stat[0], easy_time)
            # Html formating
            user_stats_lst += ['<li>{}</li>'.format(USER_STAT)]
        else:
            pass

    # print(user_stats)
    return user_stats


def get_sections_stats(sections_stats_lst, stat_logging):
    section_count = ''
    total_size = 0

    for sections in get_get_libraries():

        lib_size = get_get_library_media_info(sections['section_id'])
        total_size += lib_size

        if sections['section_type'] in ['artist', 'show', 'photo']:

            stat_dict = {'section_type': sections['section_type'],
                                   'count': sections['count'],
                                   'parent_count': sections['parent_count'],
                                   'child_count': sections['child_count'],
                                   'size': lib_size,
                                   'friendly_size': sizeof_fmt(lib_size)}

            add_to_dictlist(stat_logging['data'], sections['section_name'], stat_dict)

        if sections['section_type'] == 'artist':
            section_count = ARTIST_STAT.format(sections['count'], sections['parent_count'], sections['child_count'])

        elif sections['section_type'] == 'show':
            section_count = SHOW_STAT.format(sections['count'], sections['parent_count'], sections['child_count'])

        elif sections['section_type'] == 'photo':
            section_count = PHOTO_STAT.format(sections['count'], sections['parent_count'], sections['child_count'])

        elif sections['section_type'] == 'movie':
            section_count = MOVIE_STAT.format(sections['count'])

            stat_dict = {'section_type': sections['section_type'],
                               'count': sections['count'],
                               'size': lib_size,
                               'friendly_size': sizeof_fmt(lib_size)}

            add_to_dictlist(stat_logging['data'], sections['section_name'], stat_dict)

        else:
            pass

        if sections['section_name'] not in LIB_IGNORE and section_count:
            # Html formating
            sections_stats_lst += ['<li>{}: {}</li>'.format(sections['section_name'], section_count)]


    stat_logging['total_size'] = total_size
    stat_logging['total_size_friendly'] = sizeof_fmt(total_size)

    # Html formating. Adding the Capacity to button of list.
    sections_stats_lst += ['<li>Capacity: {}</li>'.format(sizeof_fmt(total_size))]
    # print(sections_stats)
    return sections_stats_lst


user_stats_lst = []
sections_stats_lst = []

stat_logging = {'start_date': START_DATE, 'end_date': END_DATE, 'data': {}}

users_stats = get_user_stats(user_stats_lst, stat_logging, USER_STAT)
lib_stats = get_sections_stats(sections_stats_lst, stat_logging)

# print(json.dumps(stat_logging, indent=4, sort_keys=True))

end = time.ctime(float(TODAY))
start = time.ctime(float(LASTWEEK))

sections_stats = "\n".join(sections_stats_lst)
user_stats = "\n".join(user_stats_lst)

BODY_TEXT = BODY_TEXT.format(end=end, start=start, sections_stats=sections_stats, user_stats=user_stats)

send_notification(BODY_TEXT)
