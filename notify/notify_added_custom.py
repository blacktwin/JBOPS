"""
Send an email with what was added to Plex in the past week using Tautulli.
Email includes title (TV: Show Name: Episode Name; Movie: Movie Title), time added, image, and summary.

Uses:
    notify_added_lastweek.py -t poster -d 1 -u all -i user1 user2 -s 250 100
        # email all users expect user1 & user2 what was added in the last day using posters that are 250x100

    notify_added_lastweek.py -t poster -d 7 -u all
        # email all users what was added in the last 7 days(week) using posters that are default sized

    notify_added_lastweek.py -t poster -d 7 -u all -s 1000 500
        # email all users what was added in the last 7 days(week) using posters that are 1000x500

    notify_added_lastweek.py -t art -d 7 -u user1
        # email user1 & self what was added in the last 7 days(week) using artwork that is default sized

    notify_added_lastweek.py -t art -d 7
        # email self what was added in the last 7 days(week) using artwork that is default sized

"""

import requests
import sys
import time
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import email.utils
import smtplib
import urllib
import cgi
import uuid
import argparse



## EDIT THESE SETTINGS ##
TAUTULLI_APIKEY = ''  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL
LIBRARY_NAMES = ['Movies', 'TV Shows'] # Name of libraries you want to check.

# Email settings
name = '' # Your name
sender = '' # From email address
to = [sender] # Whoever you want to email [sender, 'name@example.com']
# Emails will be sent as BCC.
email_server = 'smtp.gmail.com' # Email server (Gmail: smtp.gmail.com)
email_port = 587  # Email port (Gmail: 587)
email_username = '' # Your email username
email_password = '' # Your email password
email_subject = 'Tautulli Added Last {} day(s) Notification' #The email subject

# Default sizing for pictures
# Poster
poster_h = 205
poster_w = 100
# Artwork
art_h = 100
art_w = 205

## /EDIT THESE SETTINGS ##

class METAINFO(object):
    def __init__(self, data=None):
        d = data or {}
        self.added_at = d['added_at']
        self.parent_rating_key = d['parent_rating_key']
        self.title = d['title']
        self.rating_key = d['rating_key']
        self.media_type = d['media_type']
        self.grandparent_title = d['grandparent_title']
        self.thumb = d['art']
        self.summary = d['summary']


def get_recent(section_id, start, count):
    # Get the metadata for a media item. Count matters!
    payload = {'apikey': TAUTULLI_APIKEY,
               'start': str(start),
               'count': str(count),
               'section_id': section_id,
               'cmd': 'get_recently_added'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        if response['response']['result'] == 'success':
            res_data = response['response']['data']['recently_added']

            return res_data

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_recently_added' request failed: {0}.".format(e))


def get_metadata(rating_key):
    # Get the metadata for a media item.
    payload = {'apikey': TAUTULLI_APIKEY,
               'rating_key': rating_key,
               'cmd': 'get_metadata',
               'media_info': True}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        if response['response']['result'] == 'success':
            res_data = response['response']['data']

            return METAINFO(data=res_data)

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_metadata' request failed: {0}.".format(e))


def get_libraries_table():
    # Get the data on the Tautulli libraries table.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_libraries_table'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']['data']
        return [d['section_id'] for d in res_data if d['section_name'] in LIBRARY_NAMES]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_libraries_table' request failed: {0}.".format(e))


def update_library_media_info(section_id):
    # Get the data on the Tautulli media info tables.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_library_media_info',
               'section_id': section_id,
               'refresh': True}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.status_code
        if response != 200:
            print(r.content)

    except Exception as e:
        sys.stderr.write("Tautulli API 'update_library_media_info' request failed: {0}.".format(e))


def get_pms_image_proxy(thumb):
    # Gets an image from the PMS and saves it to the image cache directory.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'pms_image_proxy',
               'img': thumb}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload, stream=True)
        return r.url

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_users_tables' request failed: {0}.".format(e))


def get_users():
    # Get the user list from Tautulli.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_users'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']
        return [d for d in res_data]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_user' request failed: {0}.".format(e))


def get_rating_keys(TODAY, LASTDATE):

    recent_lst = []
    # Get the rating_key for what was recently added
    count = 25
    for section_id in glt:
        start = 0

        while True:
            # Assume all items will be returned in descending order of added_at
            recent_items = get_recent(section_id, start, count)

            if all([recent_items]):
                start += count
                for item in recent_items:
                    if LASTDATE <= int(item['added_at']) <= TODAY:
                        recent_lst.append(item['rating_key'])
                continue
            elif not all([recent_items]):
                break

            start += count
    if recent_lst:
        return recent_lst
    sys.stderr.write("Recently Added list: {0}.".format(recent_lst))
    exit()


def build_html(rating_key, height, width, pic_type):

    meta = get_metadata(str(rating_key))

    added = time.ctime(float(meta.added_at))
    # Pull image url
    thumb_url = "{}.jpeg".format(get_pms_image_proxy(meta.thumb))
    if pic_type == 'poster':
        thumb_url = thumb_url.replace('%2Fart%', '%2Fposter%')
    image_name = "{}.jpg".format(str(rating_key))
    # Saving image in current path
    urllib.urlretrieve(thumb_url, image_name)
    image = dict(title=meta.rating_key, path=image_name, cid=str(uuid.uuid4()))
    if meta.grandparent_title == '' or meta.media_type == 'movie':
        # Movies
        notify = u"<dt>{x.title} ({x.rating_key}) was added {when}.</dt>" \
                       u"</dt> <dd> <table> <tr> <th>" \
                       '<img src="cid:{cid}" alt="{alt}" width="{width}" height="{height}"> </th>' \
                       u" <th id=t11> {x.summary} </th> </tr> </table> </dd> <br>" \
            .format(x=meta, when=added, alt=cgi.escape(meta.rating_key), quote=True, width=width, height=height,**image)
    else:
        # Shows
        notify = u"<dt>{x.grandparent_title}: {x.title} ({x.rating_key}) was added {when}." \
                       u"</dt> <dd> <table> <tr> <th>" \
                       '<img src="cid:{cid}" alt="{alt}" width="{width}" height="{height}"> </th>' \
                       u" <th id=t11> {x.summary} </th> </tr> </table> </dd> <br>" \
            .format(x=meta, when=added, alt=cgi.escape(meta.rating_key), quote=True, width=width, height=height, **image)

    image_text = MIMEText(u'[image: {title}]'.format(**image), 'plain', 'utf-8')

    return image_text, image, notify


def send_email(msg_text_lst, notify_lst, image_lst, to, days):
    """
    Using info found here: http://stackoverflow.com/a/20485764/7286812
    to accomplish emailing inline images
    """
    msg_html = MIMEText("""\
    <html>
      <head>
        <style>
        th#t11 {{ padding: 6px; vertical-align: top; text-align: left; }}
        </style>
      </head>
      <body>
        <p>Hi!<br>
        <br>Below is the list of content added to Plex's {LIBRARY_NAMES} this week.<br>
        <dl>
        {notify_lst}
        </dl>
        </p>
      </body>
    </html>
    """.format(notify_lst="\n".join(notify_lst).encode("utf-8"), LIBRARY_NAMES=" & ".join(LIBRARY_NAMES)
               , quote=True, ), 'html', 'utf-8')

    message = MIMEMultipart('related')
    message['Subject'] = email_subject.format(days)
    message['From'] = email.utils.formataddr((name, sender))
    message_alternative = MIMEMultipart('alternative')
    message.attach(message_alternative)

    for msg_text in msg_text_lst:
        message_alternative.attach(msg_text)

    message_alternative.attach(msg_html)

    for img in image_lst:
        with open(img['path'], 'rb') as file:
            message_image_lst = [MIMEImage(file.read(), name=os.path.basename(img['path']))]

        for msg in message_image_lst:
            message.attach(msg)
            msg.add_header('Content-ID', '<{}>'.format(img['cid']))

    mailserver = smtplib.SMTP(email_server, email_port)
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.ehlo()
    mailserver.login(email_username, email_password)
    mailserver.sendmail(sender, to, message.as_string())
    mailserver.quit()
    print('Email sent')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Send an email with what was added to Plex in the past week using Tautulli.")
    parser.add_argument('-t', '--type', help='Metadata picture type from Plex.',
                        required= True, choices=['art', 'poster'])
    parser.add_argument('-s', '--size', help='Metadata picture size from Plex {Height Width}.', nargs='*')
    parser.add_argument('-d', '--days', help='Time frame for which to check recently added to Plex.',
                        required= True, type=int)
    parser.add_argument('-u', '--users', help='Which users from Plex will be emailed.',
                        nargs='+', default='self', type=str)
    parser.add_argument('-i', '--ignore', help='Which users from Plex to ignore.',
                        nargs='+', default='None', type=str)


    opts = parser.parse_args()

    TODAY = int(time.time())
    LASTDATE = int(TODAY - opts.days * 24 * 60 * 60)

    # Image sizing based on type or custom size
    if opts.type == 'poster' and not opts.size:
        height = poster_h
        width = poster_w
    elif opts.size:
        height = opts.size[0]
        width = opts.size[1]
    else:
        height = art_h
        width = art_w

    # Find the libraries from LIBRARY_NAMES
    glt = [lib for lib in get_libraries_table()]

    # Update media info for libraries.
    [update_library_media_info(i) for i in glt]

    # Gather all users email addresses
    if opts.users == ['all']:
        [to.append(x['email']) for x in get_users() if x['email'] != '' and x['email'] not in to
         and x['username'] not in opts.ignore]
    elif opts.users != ['all'] and opts.users != 'self':
        for get_users in get_users():
            for arg_users in opts.users:
                if arg_users in get_users['username']:
                    to = to + [str(get_users['email'])]
    print('Sending email(s) to {}'.format(', '.join(to)))

    # Gather rating_keys on recently added media.
    rating_keys_lst = get_rating_keys(TODAY, LASTDATE)

    # Build html elements from rating_key
    image_lst = []
    msg_text_lst = []
    notify_lst = []

    build_parts = [build_html(rating_key, height, width, opts.type) for rating_key in sorted(rating_keys_lst)]
    for parts in build_parts:
        msg_text_lst.append(parts[0])
        image_lst.append(parts[1])
        notify_lst.append(parts[2])

    # Send email
    send_email(msg_text_lst, notify_lst, image_lst, to, opts.days)

    # Delete images in current path
    for img in image_lst:
        os.remove(img['path'])
