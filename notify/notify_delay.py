"""
Delay Notification Agent message for concurrent streams

Arguments passed from Tautulli
-u {user} -srv {server_name}
You can add more arguments if you want more details in the email body

Adding to Tautulli
Tautulli > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on concurrent streams
Tautulli > Settings > Notification Agents > Scripts > Gear icon:
        User Concurrent Streams: notify_delay.py

Tautulli Settings > Notification Agents > Scripts (Gear) > Script Timeout: 0 to disable or set to > 180
"""

import requests
import sys
import argparse
from time import sleep

## EDIT THESE SETTINGS ##
TAUTULLI_APIKEY = ''  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL
CONCURRENT_TOTAL = 2
TIMEOUT = 180
INTERVAL = 20

NOTIFIER_ID = 10  # Notification notifier ID for Tautulli
# Find Notification agent ID here:
# https://github.com/JonnyWong16/plexpy/blob/master/API.md#notify

SUBJECT_TEXT = 'Concurrent Streams from {p.user} on {p.plex_server}'
BODY_TEXT = """\
        <html>
          <head></head>
          <body>
            <p>Hi!<br>
                {p.user} has had {total} concurrent streams for longer than {time} minutes.
            </p>
          </body>
        </html>
        """


def get_activity():
    # Get the current activity on the PMS.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_activity'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']['sessions']
        return [d['user'] for d in res_data]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_activity' request failed: {0}.".format(e))
        pass


def send_notification(subject_text, body_text):
    # Format notification text
    try:
        subject = subject_text.format(p=p, total=cc_total)
        body = body_text.format(p=p, total=cc_total, time=TIMEOUT / 60)

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
    parser = argparse.ArgumentParser()

    parser.add_argument('-u', '--user', action='store', default='',
                        help='Username of the person watching the stream')
    parser.add_argument('-srv', '--plex_server', action='store', default='',
                        help='The name of the Plex server')

    p = parser.parse_args()

    x = 0
    while x < TIMEOUT and x is not None:
        # check if user still has concurrent streams
        print('Checking concurrent stream count.')
        cc_total = get_activity().count(p.user)
        if cc_total >= CONCURRENT_TOTAL:
            print('{p.user} still has {total} concurrent streams.'.format(p=p, total=cc_total))
            sleep(INTERVAL)
            x += INTERVAL
        else:
            print('Exiting, user no longer has concurrent streams.')
            exit()

    print('Concurrent stream monitoring timeout limit has been reached. Sending notification.')
    send_notification(SUBJECT_TEXT, BODY_TEXT)
