"""
Notify users of recently added episode to show that they have watched at least LIMIT times via email.
Also notify users of new movies.
Block users with IGNORE_LST.

Arguments passed from Tautulli
-sn {show_name} -ena {episode_name} -ssn {season_num00} -enu {episode_num00} -srv {server_name} -med {media_type}
-pos {poster_url} -tt {title} -sum {summary} -lbn {library_name} -grk {grandparent_rating_key}
You can add more arguments if you want more details in the email body

Adding to Tautulli
Tautulli > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on recently added
Tautulli > Settings > Notification Agents > Scripts > Gear icon:
        Recently Added: notify_fav_tv_all_movie.py
"""

import requests
from email.mime.text import MIMEText
import email.utils
import smtplib
import sys
import argparse

## EDIT THESE SETTINGS ##
TAUTULLI_APIKEY = 'XXXXXXX'  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL

IGNORE_LST = ['123456', '123456'] # User_ids
LIMIT = 3

# Email settings
name = ''  # Your name
sender = ''  # From email address
email_server = 'smtp.gmail.com'  # Email server (Gmail: smtp.gmail.com)
email_port = 587  # Email port (Gmail: 587)
email_username = ''  # Your email username
email_password = ''  # Your email password

# Detailed subject and body for movie.
# You can add more arguments if you want more details in the email subject and body
MOVIE_SUBJECT = 'Good News Everybody! A new {p.media_type} is available on {p.plex_server}'
MOVIE_BODY = """\
            <html>
              <head></head>
              <body>
                <p>Hi!<br>
                    {p.title} -- was recently added to {p.library_name} on PLEX
                    <br><br>
                    <br> {p.summary} <br>
                   <br><img src="{p.poster}" alt="Poster unavailable" height="150" width="102"><br>
                </p>
              </body>
            </html>
            """

# Detailed subject and body for tv shows.
# You can add more arguments if you want more details in the email subject and body
TV_SUBJECT = 'New episode for {p.show_name} is available on {p.plex_server}'
TV_BODY = """\
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

user_dict = {}

class Users(object):
    def __init__(self, data=None):
        d = data or {}
        self.email = d['email']
        self.user_id = d['user_id']


class UserHIS(object):
    def __init__(self, data=None):
        d = data or {}
        self.watched = d['watched_status']
        self.title = d['full_title']
        self.user = d['friendly_name']
        self.user_id = d['user_id']
        self.media = d['media_type']
        self.rating_key = d['rating_key']
        self.show_key = d['grandparent_rating_key']


def get_user(user_id):
    # Get the user list from Tautulli.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_user',
               'user_id': int(user_id)}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']
        return Users(data=res_data)

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_user' request failed: {0}.".format(e))

def get_users():
    # Get the user list from Tautulli.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_users'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']
        return res_data

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_user' request failed: {0}.".format(e))


def get_history(showkey):
    # Get the user history from Tautulli. Length matters!
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'grandparent_rating_key': int(showkey),
               'length': 10000}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']['data']
        return [UserHIS(data=d) for d in res_data if d['watched_status'] == 1
                and d['media_type'].lower() in ('episode', 'show')]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))


def add_to_dictlist(d, key, val):
    if key not in d:
        d[key] = [val]
    else:
        d[key].append(val)


def get_email(show):
    history = get_history(show)

    [add_to_dictlist(user_dict, h.user_id, h.show_key) for h in history]
    # {user_id1: [grand_key, grand_key], user_id2: [grand_key]}

    for key, value in user_dict.items():
        user_dict[key] = {x: value.count(x) for x in value}
        # Count how many times user watched show. History length matters!
        # {user_id1: {grand_key: 2}, user_id2: {grand_key: 1}

    email_lst = []

    user_lst = user_dict.keys()

    for i in user_lst:
        try:
            if user_dict[i][show] > LIMIT:
                g = get_user(i)
                if g.user_id not in IGNORE_LST:
                    sys.stdout.write("Sending {g.user_id} email for %s.".format(g=g) % show)
                    email_lst += [g.email]
        except Exception as e:
            sys.stderr.write("An error occurred gathering email addresses: {0}".format(e))
            pass
    return (email_lst)


def send_email(to, email_subject, body_html):
    ### Do not edit below ###
    message = MIMEText(body_html, 'html')
    message['Subject'] = email_subject
    message['From'] = email.utils.formataddr((name, sender))

    mailserver = smtplib.SMTP(email_server, email_port)
    mailserver.starttls()
    mailserver.ehlo()
    mailserver.login(email_username, email_password)
    mailserver.sendmail(sender, to, message.as_string())
    mailserver.quit()
    print 'Email sent'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-ip', '--ip_address', action='store', default='',
                        help='The IP address of the stream')
    parser.add_argument('-us', '--user', action='store', default='',
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

    if p.media_type == 'movie':
        email_subject = MOVIE_SUBJECT.format(p=p)
        to = filter(None, [x['email'] for x in get_users() if x['user_id'] not in IGNORE_LST])
        body_html = MOVIE_BODY.format(p=p)
        send_email(to, email_subject, body_html)

    elif p.media_type in  ['show', 'season', 'episode']:
        email_subject = TV_SUBJECT.format(p=p)
        to = get_email(int(p.grandparent_rating_key))
        body_html = TV_BODY.format(p=p)
        send_email(to, email_subject, body_html)
    else:
        sys.stderr.write('Media Type is not TV or Movie. Killing script.')
        exit()
