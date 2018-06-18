"""
Description: Use conditions to kill a stream
Author: Blacktwin, Arcanemagus, samwiseg00
Requires: requests

Adding the script to Tautulli:
Taultulli > Settings > Notification Agents > Add a new notification agent >
 Script

Configuration:
Taultulli > Settings > Notification Agents > New Script > Configuration:

 Script Folder: /path/to/your/scripts
 Script File: ./kill_stream.py (Should be selectable in a dropdown list)
 Script Timeout: {timeout}
 Description: Kill stream(s)
 Save

Triggers:
Taultulli > Settings > Notification Agents > New Script > Triggers:

 Check: Playback Start and/or Playback Pause
 Save

Conditions:
Taultulli > Settings > Notification Agents > New Script > Conditions:

 Set Conditions: [{condition} | {operator} | {value} ]
 Save

Script Arguments:
Taultulli > Settings > Notification Agents > New Script > Script Arguments:

 Select: Playback Start, Playback Pause
 Arguments: --jbop SELECTOR --userId {user_id} --username {username}
            --sessionId {session_id} --notify notifierID
            --interval 30 --limit 1200
            --killMessage Your message here. No quotes.

 Save
 Close

Examples:

Kill any transcoding streams
Script Timeout: 30 (default)
Triggers: Playback Start
Conditions: Transcode Decision is transcode
Arguments (Playback Start): --jbop stream --sessionId {session_id}
  --username {username}
  --killMessage Transcoding streams are not allowed on this server.

Kill all streams started by a specific user
Script Timeout: 30 (default)
Triggers: Playback Start
Conditions: Username is Bob
Arguments (Playback Start): --jbop allStreams --userId {user_id}
  --username {username}
  --killMessage Hey Bob, we need to talk!

Kill all WAN streams paused longer than 20 minutes, checking every 30 seconds
Script Timeout: 0
Triggers: Playback Pause
Conditions: Stream Location is not LAN
Arguments (Playback Start): --jbop paused --sessionId {session_id}
  --limit 1200 --interval 30
  --killMessage Your stream was paused for over 20 minutes and has been
  automatically stopped for you.

Notes:
* Any of these can have "--notify X" added to them, where X is the
ID shown in Tautulli for a Notification agent, if specified it will send a
message there when a stream is terminated.
* Arguments should all be on one line in Tautulli, they are split here for
easier reading.

"""

import requests
import argparse
import sys
import os
from time import sleep
from datetime import datetime

TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''
TAUTULLI_URL = os.getenv('TAUTULLI_URL', TAUTULLI_URL)
TAUTULLI_APIKEY = os.getenv('TAUTULLI_APIKEY', TAUTULLI_APIKEY)

SUBJECT_TEXT = "Tautulli has killed a stream."
BODY_TEXT = "Killed session ID '{id}'. Reason: {message}"
BODY_TEXT_USER = "Killed {user}'s stream. Reason: {message}."

sess = requests.Session()
# Ignore verifying the SSL certificate
sess.verify = False  # '/path/to/certfile'
# If verify is set to a path to a directory,
# the directory must have been processed using the c_rehash utility supplied
# with OpenSSL.
if sess.verify is False:
    # Disable the warning that the request is insecure, we know that...
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SELECTOR = ['stream', 'allStreams', 'paused']


def send_notification(subject_text, body_text, notifier_id):
    """Send a notification through Tautulli

    Parameters
    ----------
    subject_text : str
        The text to use for the subject line of the message.
    body_text : str
        The text to use for the body of the notification.
    notifier_id : int
        Tautulli Notification Agent ID to send the notification to.
    """
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'notify',
               'notifier_id': notifier_id,
               'subject': subject_text,
               'body': body_text}

    try:
        r = sess.post(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        if response['response']['result'] == 'success':
            sys.stdout.write("Successfully sent Tautulli notification.")
        else:
            raise Exception(response['response']['message'])
    except Exception as e:
        sys.stderr.write(
            "Tautulli API 'notify' request failed: {0}.".format(e))
        return None


def get_activity():
    """Get the current activity on the PMS.

    Returns
    -------
    list
        The current active sessions on the Plex server.
    """
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_activity'}

    try:
        req = sess.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = req.json()

        res_data = response['response']['data']['sessions']
        return res_data

    except Exception as e:
        sys.stderr.write(
            "Tautulli API 'get_activity' request failed: {0}.".format(e))
        pass


def get_user_session_ids(user_id):
    """Get current session IDs for a specific user.

    Parameters
    ----------
    user_id : int
        The ID of the user to grab sessions for.

    Returns
    -------
    list
        The active session IDs for the specific user ID.

    """
    sessions = get_activity()
    user_streams = [s['session_id']
                    for s in sessions if s['user_id'] == user_id]
    return user_streams


def terminate_session(session_id, message, notifier=None, username=None):
    """Stop a streaming session.

    Parameters
    ----------
    session_id : str
        The session ID of the stream to terminate.
    message : str
        The message to display to the user when terminating a stream.
    notifier : int
        Notification agent ID to send a message to (the default is None).
    username : str
        The username for the terminated session (the default is None).
    """
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'terminate_session',
               'session_id': session_id,
               'message': message}

    try:
        req = sess.post(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = req.json()

        if response['response']['result'] == 'success':
            sys.stdout.write(
                "Successfully killed Plex session: {0}.".format(session_id))
            if notifier:
                if username:
                    body = BODY_TEXT_USER.format(user=username,
                                                 message=message)
                else:
                    body = BODY_TEXT.format(id=session_id, message=message)
                send_notification(SUBJECT_TEXT, body, notifier)
        else:
            raise Exception(response['response']['message'])
    except Exception as e:
        sys.stderr.write(
            "Tautulli API 'terminate_session' request failed: {0}.".format(e))
        return None


def terminate_long_pause(session_id, message, limit, interval, notify=None):
    """Kills the session if it is paused for longer than <limit> seconds.

    Parameters
    ----------
    session_id : str
        The session id of the session to monitor.
    message : str
        The message to use if the stream is terminated.
    limit : int
        The number of seconds the session is allowed to remain paused before it
        is terminated.
    interval : int
        The amount of time to wait between checks of the session state.
    notify : int
        Tautulli Notification Agent ID to send a notification to on killing a
        stream.
    """
    start = datetime.now()
    checked_time = 0
    # Continue checking 2 intervals past the allowed limit in order to
    # account for system variances.
    check_limit = limit + (interval * 2)

    while checked_time < check_limit:
        sessions = get_activity()
        found_session = False

        for session in sessions:
            if session['session_id'] == session_id:
                found_session = True
                state = session['state']
                now = datetime.now()
                checked_time = (now - start).total_seconds()

                if state == 'paused':
                    if checked_time >= limit:
                        terminate_session(session_id, message, notify)
                        return
                    else:
                        sleep(interval)
                elif state == 'playing' or state == 'buffering':
                    sys.stdout.write(
                        "Session '{}' has resumed, ".format(session_id) +
                        "stopping monitoring.")
                    return
        if not found_session:
            sys.stdout.write(
                "Session '{}' is no longer active ".format(session_id) +
                "on the server, stopping monitoring.")
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Killing Plex streams from Tautulli.")
    parser.add_argument('--jbop', required=True, choices=SELECTOR,
                        help='Kill selector.\nChoices: (%(choices)s)')
    parser.add_argument('--userId', type=int,
                        help='The unique identifier for the user.')
    parser.add_argument('--username',
                        help='The username of the person streaming.')
    parser.add_argument('--sessionId', required=True,
                        help='The unique identifier for the stream.')
    parser.add_argument('--notify', type=int,
                        help='Notification Agent ID number to Agent to send ' +
                             'notification.')
    parser.add_argument('--limit', type=int, default=(20 * 60),  # 20 minutes
                        help='The time session is allowed to remain paused.')
    parser.add_argument('--interval', type=int, default=30,
                        help='The seconds between paused session checks.')
    parser.add_argument('--killMessage', nargs='+',
                        help='Message to send to user whose stream is killed.')

    opts = parser.parse_args()

    if opts.killMessage:
        message = ' '.join(opts.killMessage)
    else:
        message = ''

    if opts.jbop == 'stream':
        terminate_session(opts.sessionId, message, opts.notify, opts.username)
    elif opts.jbop == 'allStreams':
        streams = get_user_session_ids(opts.userId)
        for session_id in streams:
            terminate_session(session_id, message, opts.notify, opts.username)
    elif opts.jbop == 'paused':
        terminate_long_pause(opts.sessionId, message, opts.limit,
                             opts.interval, opts.notify)
