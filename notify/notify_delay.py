'''
Delay Notification Agent message for concurrent streams

Arguments passed from PlexPy
-u {user} -srv {server_name}
You can add more arguments if you want more details in the email body

Adding to PlexPy
PlexPy > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on concurrent streams
PlexPy > Settings > Notification Agents > Scripts > Gear icon:
        User Concurrent Streams: notify_delay.py

PlexPy Settings > Notification Agents > Scripts (Gear) > Script Timeout: 0 to disable or set to > 180
'''

import requests
import sys
import argparse
from time import sleep


## EDIT THESE SETTINGS ##
PLEXPY_APIKEY = 'xxxxx'  # Your PlexPy API key
PLEXPY_URL = 'http://localhost:8182/'  # Your PlexPy URL
CONCURRENT_TOTAL = 2
TIMEOUT = 180
INTERVAL = 20

AGENT_ID = 10  # Notification agent ID for PlexPy
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


def get_get_activity():
    # Get the current activity on the PMS.
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_activity'}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']['sessions']
        return [d['user'] for d in res_data]

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_activity' request failed: {0}.".format(e))
        pass

def send_notification(SUBJECT_TEXT, BODY_TEXT):
    # Format notification text
    try:
        subject = SUBJECT_TEXT.format(p=p, total=cc_total)
        body = BODY_TEXT.format(p=p, total=cc_total, time=TIMEOUT/60)

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
        cc_total = get_get_activity().count(p.user)
        if cc_total >= CONCURRENT_TOTAL:
            print('{p.user} still has {total} concurrent streams.'.format(p=p, total=cc_total))
            sleep(INTERVAL)
            x += INTERVAL
        else:
            print('Exiting, user no longer has concurrent streams.')
            exit()

    print('Concurrent stream monitoring timeout limit has been reached. Sending notification.')
    send_notification(SUBJECT_TEXT, BODY_TEXT)
