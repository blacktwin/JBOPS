#   1. Install the requests module for python.
#       pip install requests
#   2. Add script arguments in PlexPy.
#       {user} {title}
#   Add to Playback Resume

import requests
import ConfigParser
import io
import sys

user = sys.argv[1]
title = sys.argv[2]

# Load the configuration file
with open("../config.ini") as f:
    real_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=False)
config.readfp(io.BytesIO(real_config))

PLEXPY_APIKEY=config.get('plexpy-data', 'PLEXPY_APIKEY')
PLEXPY_URL=config.get('plexpy-data', 'PLEXPY_URL')

## EDIT THESE SETTINGS ##
AGENT_ID = 10  # The notification agent ID for PlexPy

SUBJECT_TEXT = "PlexPy Notification"
BODY_TEXT = """\
<html>
  <head></head>
  <body>
    <p>Hi!<br>
    <br>User %s has attempted to watch %s more than 3 times unsuccessfully.<br>
    </p>
  </body>
</html>
""" %(user, title)


class UserHIS(object):
    def __init__(self, data=None):
        data = data or {}
        self.watched = [d['watched_status'] for d in data]

def get_get_history():
    # Get the user IP list from PlexPy
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_history',
               'user': user,
               'search': title}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        if response['response']['data']['recordsFiltered'] > 2:
            res_data = response['response']['data']['data']
            return UserHIS(data=res_data)

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_get_history' request failed: {0}.".format(e))


def send_notification():
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


if __name__ == '__main__':
    hisy = get_get_history()

    if sum(hisy.watched) == 0:
        sys.stdout.write(user + ' has attempted to watch ' + title + ' more than 3 times unsuccessfully.')
        send_notification()
