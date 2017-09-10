'''
Delay Notification Agent messages

Arguments passed from PlexPy
-sn {show_name} -ena {episode_name} -ssn {season_num00} -enu {episode_num00} -srv {server_name} -med {media_type}
-pos {poster_url} -tt {title} -sum {summary} -lbn {library_name} -grk {grandparent_rating_key} -un {username}
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
PLEXPY_APIKEY = 'XXXXXX'  # Your PlexPy API key
PLEXPY_URL = 'http://localhost:8181/'  # Your PlexPy URL

AGENT_ID = 16  # Notification agent ID for PlexPy

# Find Notification agent ID here:
# https://github.com/JonnyWong16/plexpy/blob/master/API.md#notify

SUBJECT_TEXT = 'Concurrent Stream from {p.username} on {p.plex_server}'
BODY_TEXT = """\
        <html>
          <head></head>
          <body>
            <p>Hi!<br>
                {p.show_name}  S{p.season_num} - E{p.episode_num} -- {p.episode_name} -- was recently added to
                {p.library_name} on PLEX
                <br><br>
                <br> {p.summary} <br>
               <br><img src="{p.poster}" alt="Poster unavailable" height="150" width="102"><br>
            </p>
          </body>
        </html>
        """


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

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-ip', '--ip_address', action='store', default='',
                        help='The IP address of the stream')
    parser.add_argument('-un', '--username', action='store', default='',
                        help='Username of the person watching the stream')
    parser.add_argument('-uid', '--user_id', action='store', default='',
                        help='User_ID of the person watching the stream')
    parser.add_argument('-med', '--media_type', action='store', default='',
                        help='The media type of the stream')
    parser.add_argument('-tt', '--title', action='store', default='',
                        help='The title of the media')
    parser.add_argument('-pf', '--platform', action='store', default='',
                        help='The platform of the stream')
    parser.add_argument('-pl', '--player', action='store', default='',
                        help='The player of the stream')
    parser.add_argument('-da', '--datestamp', action='store', default='',
                        help='The date of the stream')
    parser.add_argument('-ti', '--timestamp', action='store', default='',
                        help='The time of the stream')
    parser.add_argument('-sn', '--show_name', action='store', default='',
                        help='The name of the TV show')
    parser.add_argument('-ena', '--episode_name', action='store', default='',
                        help='The name of the episode')
    parser.add_argument('-ssn', '--season_num', action='store', default='',
                        help='The season number of the TV show')
    parser.add_argument('-enu', '--episode_num', action='store', default='',
                        help='The episode number of the TV show')
    parser.add_argument('-srv', '--plex_server', action='store', default='',
                        help='The name of the Plex server')
    parser.add_argument('-pos', '--poster', action='store', default='',
                        help='The poster url')
    parser.add_argument('-sum', '--summary', action='store', default='',
                        help='The summary of the TV show')
    parser.add_argument('-lbn', '--library_name', action='store', default='',
                        help='The name of the TV show')
    parser.add_argument('-grk', '--grandparent_rating_key', action='store', default='',
                        help='The key of the TV show')
    parser.add_argument('-purl', '--plex_url', action='store', default='',
                        help='Url to Plex video')

    p = parser.parse_args()

    sleep(240) # wait 240 seconds
    send_notification(BODY_TEXT.format(p=p))
