#   1. Install the requests module for python.
#       pip install requests
#   2. Add script arguments in Tautulli.
#       {user} {title}
#   Add to Playback Resume

import requests
import sys

user = sys.argv[1]
title = sys.argv[2]

## EDIT THESE SETTINGS ##
TAUTULLI_APIKEY = 'XXXXXXXXXX'  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL
NOTIFIER_ID = 10  # The notification notifier ID for Tautulli

SUBJECT_TEXT = "Tautulli Notification"
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

		
def get_history():
    # Get the user IP list from Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'user': user,
               'search': title}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        if response['response']['data']['recordsFiltered'] > 2:
            res_data = response['response']['data']['data']
            return UserHIS(data=res_data)

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))


def send_notification():
    # Format notification text
    try:
        subject = SUBJECT_TEXT
        body = BODY_TEXT
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


if __name__ == '__main__':
    hisy = get_history()

    if sum(hisy.watched) == 0:
        sys.stdout.write(user + ' has attempted to watch ' + title + ' more than 3 times unsuccessfully.')
        send_notification()
