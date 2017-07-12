"""
Use PlexPy to count how many plays per user occurred this week.
Notify via PlexPy Notification
"""

import requests
import sys
import time

TODAY = int(time.time())
LASTWEEK = int(TODAY - 7 * 24 * 60 * 60)

## EDIT THESE SETTINGS ##
PLEXPY_APIKEY = 'XXXXXX'  # Your PlexPy API key
PLEXPY_URL = 'http://localhost:8181/'  # Your PlexPy URL
SUBJECT_TEXT = "PlexPy Weekly Plays Per User"
AGENT_ID = 10  # The email notification agent ID for PlexPy


class UserHIS(object):
    def __init__(self, data=None):
        d = data or {}
        self.watched = d['watched_status']
        self.title = d['full_title']
        self.user = d['friendly_name']
        self.user_id = d['user_id']
        self.media = d['media_type']
        self.rating_key = d['rating_key']
        self.full_title = d['full_title']
        self.date = d['date']

def get_get_history():
    # Get the PlexPy history. Count matters!!!
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_history',
               'length': 100000}
               
    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return [UserHIS(data=d) for d in res_data if d['watched_status'] == 1 and
                LASTWEEK < d['date'] < TODAY]
    
    except Exception as e:
        sys.stderr.write("PlexPy API 'get_history' request failed: {0}.".format(e))

def send_notification(BODY_TEXT):
    # Format notification text
    try:
        subject = SUBJECT_TEXT
        body = BODY_TEXT
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

user_dict ={}
notify_lst = []

[add_to_dictlist(user_dict, h.user, h.media) for h in get_get_history()]
# Get count of media_type play in time frame
for key, value in user_dict.items():
    user_dict[key] = {x: value.count(x) for x in value}
# Get total of all media_types play in time frame
for key, value in user_dict.items():
    user_dict[key].update({'total': sum(value.values())})
# Build email body contents
for key, value in user_dict.items():
    notify_lst += [u"<dt>{} played a total of {} item(s) this week.</dt>".format(key, user_dict[key]['total'])]


BODY_TEXT = """\
<html>
  <head></head>
  <body>
    <p>Hi!<br>
    <br>Below is the list of plays per user this week ({start} - {end})<br>
    <dl>
    {notify_lst}
    </dl>
    </p>
  </body>
</html>
""".format(notify_lst="\n".join(notify_lst).encode("utf-8"),end=time.ctime(float(TODAY)),
           start=time.ctime(float(LASTWEEK)))

send_notification(BODY_TEXT)
