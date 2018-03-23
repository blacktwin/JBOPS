"""
1. Install the requests module for python.
       pip install requests
       pip install twitter

Tautulli > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on Recently Added
Tautulli > Settings > Notification Agents > Scripts > Gear icon:
        Playback Recently Added: twitter_notify.py
Tautulli > Settings > Notifications > Script > Script Arguments:
        -sn {show_name} -ena {episode_name} -ssn {season_num00} -enu {episode_num00} -dur {duration}
        -srv {server_name} -med {media_type} -tt {title} -purl {plex_url} -post {poster_url}

https://gist.github.com/blacktwin/261c416dbed08291e6d12f6987d9bafa
"""

from twitter import *
import argparse
import requests
import os

## EDIT THESE SETTINGS ##
TOKEN = ''
TOKEN_SECRET = ''
CONSUMER_KEY = ''
CONSUMER_SECRET = ''

TITLE_FIND = ['Friends'] # Title to ignore ['Snow White']
TWITTER_USER = ' @username'

BODY_TEXT = ''
MOVIE_TEXT = "New {media_type}: {title} [ duration: {duration} mins ] was recently added to PLEX"
TV_TEXT = "New {media_type} of {show_name}: {title} [ S{season_num00}E{episode_num00} ] " \
          "[ duration: {duration} mins ] was recently added to PLEX"


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
    parser.add_argument('-dur', '--duration', action='store', default='',
                        help='The time of the stream')

    p = parser.parse_args()


    if p.media_type == 'movie':
        BODY_TEXT = MOVIE_TEXT.format(media_type=p.media_type, title=p.title, duration=p.duration)
    elif p.media_type == 'episode':
        BODY_TEXT = TV_TEXT.format(media_type=p.media_type, show_name=p.show_name, title=p.title,
                                   season_num00=p.season_num, episode_num00=p.episode_num, duration=p.duration)
    else:
        exit()

    if p.title in TITLE_FIND:
        BODY_TEXT += TWITTER_USER

    t = Twitter(auth=OAuth(TOKEN, TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET))

    filename = 'temp.jpg'
    request = requests.get(p.poster, stream=True)
    if request.status_code == 200:
        with open(filename, 'wb') as image:
            for chunk in request:
                image.write(chunk)


    t_upload = Twitter(domain='upload.twitter.com',
                       auth=OAuth(TOKEN, TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET))

    file = open(filename, 'rb')
    data = file.read()
    id_img1 = t_upload.media.upload(media=data)["media_id_string"]

    t.statuses.update(status=BODY_TEXT, media_ids=",".join([id_img1]))

    os.remove(filename)
