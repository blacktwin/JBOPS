"""
Share functions from https://gist.github.com/JonnyWong16/f8139216e2748cb367558070c1448636

Once user stream count hits LIMIT they are unshared from libraries expect for banned library.
Once user stream count is below LIMIT and banned library video is watched their shares are restored.
Once violation count have been reached ban permanently.

Caveats:
    Unsharing doesn't pause the stream.
    After unsharing user can pause but not skip ahead or skip back.
    Going from unshared to shared while playing still kills the connection to the server.
    Effected user will need to refresh browser/app or restart app to reconnect.
    User watch record stop when unshare is executed.
    If user finishes a movie/show while unshared they will not have that record.
    Tautulli will not have that record.

Adding to Tautulli

Tautulli > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start
        [X] Notify on watched

Tautulli > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: stream_limiter_ban_email.py
        Playback Watched: stream_limiter_ban_email.py

If used in Tautulli:
Tautulli will continue displaying that user is watching after unshare is executed in ACTIVITY.
Tautulli will update after ~5 minutes and no longer display user's stream in ACTIVITY.
Tautulli will think that user has stopped.


Create new library with one video.
Name library and video whatever you want.

My suggestion:
    Video: https://www.youtube.com/watch?v=dQw4w9WgXcQ
    Video Summary: "You have been banned for one reason or another. Please watch this video to become un-banned.
        The entire video must be watched in order to trigger un-ban."
Change Video Poster and Background.
Entire video needs to be watched to trigger normal sharing.

This is indented to restrict a user to the LIMIT amount of concurrent streams. User will be warned, punished, and
banned completely if violations continue.

Clear user history for banned video to remove violation counts and run manually to share again.

Concurrent stream count is the trigger. Trigger can be anything you want.

"""


import requests
import sys
from xml.dom import minidom
from email.mime.text import MIMEText
import email.utils
import smtplib


## EDIT THESE SETTINGS ###

TAUTULLI_APIKEY = 'XXXXXX'  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL
PLEX_TOKEN = "<token>"
SERVER_ID = "XXXXX"  # Example: https://i.imgur.com/EjaMTUk.png

# Get the User IDs and Library IDs from
# https://plex.tv/api/servers/SERVER_ID/shared_servers
# Example: https://i.imgur.com/yt26Uni.png
# Enter the User IDs and Library IDs in this format below:
#     {UserID1: [LibraryID1, LibraryID2],
#      UserID2: [LibraryID1, LibraryID2]}

USER_LIBRARIES = {123456: [123456, 123456, 123456, 123456, 123456, 123456]}
BAN_LIBRARY = {123456: [123456]} # {UserID1: [LibraryID1], UserID2: [LibraryID1]}
BAN_RATING = 123456 # Banned rating_key to check if it's been watched.

LIMIT = 3
VIOLATION_LIMIT = 3

FIRST_WARN = 'Please watch this video to become un-banned. The whole video must be watched in order to trigger un-ban.'
FINAL_WARN = '3 Strikes you are out! You are permanently banned from my Plex.'

SUBJECT_TEXT = "Plex rules have been violated."
BODY_TEXT = """\
<html>
  <head></head>
  <body>
    <p>Hello,<br>
    <br>{f}, you have been banned from my Plex and unshared from most of my libraries.
    This is your violation {v} of {vt}.<br>
    <br>{m}<br>
    <br><br>
    </p>
  </body>
</html>
"""

# Email settings
name = '' # Your name
sender = '' # From email address
email_server = 'smtp.gmail.com' # Email server (Gmail: smtp.gmail.com)
email_port = 587  # Email port (Gmail: 587)
email_username = '' # Your email username
email_password = '' # Your email password


## DO NOT EDIT BELOW ##

class Activity(object):
    def __init__(self, data=None):
        d = data or {}
        self.rating_key = d['rating_key']
        self.title = d['full_title']
        self.user = d['user']
        self.user_id = d['user_id']
        self.video_decision = d['video_decision']
        self.transcode_decision = d['transcode_decision']
        self.transcode_key = d['transcode_key']
        self.state = d['state']

class Users(object):
    def __init__(self, data=None):
        d = data or {}
        self.email = d['email']
        self.user_id = d['user_id']
        self.friendly_name = d['friendly_name']

def get_user(user_id):
    # Get the user list from Tautulli.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_user',
               'user_id': int(user_id)}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        email = response['response']['data']['email']
        friend_name = response['response']['data']['friendly_name']
        return [email, friend_name]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_user' request failed: {0}.".format(e))


def get_history(user_id, bankey):
    # Get the user history from Tautulli. Length matters!
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'rating_key': bankey,
               'user_id': user_id,
               'length': 10000}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        rec_filtered = response['response']['data']['recordsFiltered']
        # grow this out how you will
        if rec_filtered < VIOLATION_LIMIT:
            return rec_filtered
        elif rec_filtered >= VIOLATION_LIMIT:
            return 'ban'

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))

def share(user_id, ban):

    headers = {"X-Plex-Token": PLEX_TOKEN,
               "Accept": "application/json"}

    url = "https://plex.tv/api/servers/" + SERVER_ID + "/shared_servers"

    if ban == 1:
        library_ids = BAN_LIBRARY[user_id]
    else:
        library_ids = USER_LIBRARIES[user_id]

    payload = {"server_id": SERVER_ID,
               "shared_server": {"library_section_ids": library_ids,
                                 "invited_id": user_id}
               }

    r = requests.post(url, headers=headers, json=payload)

    if r.status_code == 401:
        print("Invalid Plex token")
        return

    elif r.status_code == 400:
        print(r.content)
        return r.status_code

    elif r.status_code == 200:
        print("Shared libraries with user %s" % str(user_id))
        return

    return

def unshare(user_id):

    headers = {"X-Plex-Token": PLEX_TOKEN,
               "Accept": "application/json"}

    url = "https://plex.tv/api/servers/" + SERVER_ID + "/shared_servers"
    r = requests.get(url, headers=headers)

    if r.status_code == 401:
        print("Invalid Plex token")
        return

    elif r.status_code == 400:
        print r.content
        return

    elif r.status_code == 200:
        response_xml = minidom.parseString(r.content)
        MediaContainer = response_xml.getElementsByTagName("MediaContainer")[0]
        SharedServer = MediaContainer.getElementsByTagName("SharedServer")

        shared_servers = {int(s.getAttribute("userID")): int(s.getAttribute("id"))
                          for s in SharedServer}

        server_id = shared_servers.get(user_id)

        if server_id:
            url = "https://plex.tv/api/servers/" + SERVER_ID + "/shared_servers/" + str(server_id)
            r = requests.delete(url, headers=headers)

            if r.status_code == 200:
                print("Unshared libraries with user %s" % str(user_id))

        else:
            print("No libraries shared with user %s" % str(user_id))

    return

def get_activity():
    # Get the user IP list from Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_activity'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']['sessions']
        return [Activity(data=d) for d in res_data]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_activity' request failed: {0}.".format(e))

def send_notification(to=None, friendly=None, val_cnt=None, val_tot=None, mess=None):
    # Format notification text
    try:
        email_subject = SUBJECT_TEXT
        body = BODY_TEXT.format(f=friendly, v=val_cnt, vt=val_tot, m=mess)

        message = MIMEText(body, 'html')
        message['Subject'] = email_subject
        message['From'] = email.utils.formataddr((name, sender))

        mailserver = smtplib.SMTP(email_server, email_port)
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.ehlo()
        mailserver.login(email_username, email_password)
        mailserver.sendmail(sender, to, message.as_string())
        mailserver.quit()
        print('Email sent')
    except Exception as e:
        sys.stderr.write("Email Failure: {0}.".format(e))


if __name__ == "__main__":

    activity = get_activity()

    act_lst = [a.user_id for a in activity]
    user_lst = [key for key, value in USER_LIBRARIES.iteritems()]

    BAN = 1
    UNBAN = 0

    for user in user_lst:
        history = get_history(user, BAN_RATING)
        mail_add, friendly = get_user(user)

        try:
            if act_lst.count(user) >= LIMIT:
                # Trigger for first and next violation
                unshare(user) # Remove libraries
                share(user, BAN) # Share banned library
                sys.stdout.write("Shared BAN_LIBRARY with user {0}".format(i))
                if type(history) is int:
                    # Next violation, history of banned video.
                    send_notification(mail_add, friendly, history, VIOLATION_LIMIT, FIRST_WARN)
                else:
                    # First violation, no history of banned video.
                    send_notification(mail_add, friendly, 1, VIOLATION_LIMIT, FIRST_WARN)
                # email address, friendly name, violation number, violation limit, message
            elif type(history) is int:
                # Trigger to share
                if share(user, UNBAN) == 400:
                    exit() # User has history of watching banned video but libraries are already restored.
                else:
                    unshare(user) # Remove banned library
                    share(user, UNBAN) # Restore libraries
            elif history == 'ban':
                # Trigger for ban
                unshare(user)
                send_notification(mail_add, friendly, VIOLATION_LIMIT, VIOLATION_LIMIT, FINAL_WARN)
                # email address, friendly name, violation number, violation limit, message
                sys.stdout.write("User {0} has been banned".format(user))
        except Exception as e:
            sys.stderr.write("Share_unshare failed: {0}.".format(e))
