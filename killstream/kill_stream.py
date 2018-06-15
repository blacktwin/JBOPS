"""
Description: Use conditions to kill a stream
Author: Blacktwin
Requires: requests

Enabling Scripts in Tautulli:
Taultulli > Settings > Notification Agents > Add a Notification Agent > Script

Configuration:
Taultulli > Settings > Notification Agents > New Script > Configuration:

 Script Name: kill_stream
 Set Script Timeout: {timeout}
 Description: Kill stream(s)
 Save

Triggers:
Taultulli > Settings > Notification Agents > New Script > Triggers:

 Check: {trigger}
 Save

Conditions:
Taultulli > Settings > Notification Agents > New Script > Conditions:

 Set Conditions: [{condition} | {operator} | {value} ]
 Save

Script Arguments:
Taultulli > Settings > Notification Agents > New Script > Script Arguments:

 Select: Playback Start, Playback Pause
 Arguments: --jbop SELECTOR --userId {user_id} --username {username}
            --sessionId {session_id} --killMessage Your message here. No quotes. --notify notifierID

 Save
 Close

"""

import requests
import argparse
import sys
import os

TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''
TAUTULLI_URL = os.getenv('TAUTULLI_URL', TAUTULLI_URL)
TAUTULLI_APIKEY = os.getenv('TAUTULLI_APIKEY', TAUTULLI_APIKEY)

SUBJECT_TEXT = "Tautulli has killed a stream."
BODY_TEXT = "Killed {user}'s stream. Reason: {message}."

sess = requests.Session()
# Ignore verifying the SSL certificate
sess.verify = False # '/path/to/certfile'
# If verify is set to a path to a directory,
# the directory must have been processed using the c_rehash utility supplied with OpenSSL.

SELECTOR = ['stream', 'allStreams']


def send_notification(subject_text, body_text, notifier_id):
    # Send the notification through Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'notify',
               'notifier_id': notifier_id,
               'subject': subject_text,
               'body': body_text}

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


def get_activity(user_id):
    # Get the current activity on the PMS.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_activity'}

    try:
        req = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = req.json()

        res_data = response['response']['data']['sessions']
        user_streams = [d['session_id'] for d in res_data if d['user_id'] == user_id]
        return user_streams

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_activity' request failed: {0}.".format(e))
        pass


def terminate_session(session_id, message):
    # Stop a streaming session.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'terminate_session',
               'session_id': session_id,
               'message': message}

    try:
        req = sess.post(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = req.json()

        if response['response']['result'] == 'success':
            sys.stdout.write("Successfully killed Plex session: {0}.".format(session_id))
        else:
            raise Exception(response['response']['message'])
    except Exception as e:
        sys.stderr.write("Tautulli API 'terminate_session' request failed: {0}.".format(e))
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Killing Plex streams from Tautulli.")
    parser.add_argument('--jbop', required=True, choices=SELECTOR,
                        help='Kill selector.\nChoices: (%(choices)s)')
    parser.add_argument('--userId', type=int,
                        help='The unique identifier for the user.')
    parser.add_argument('--username',
                        help='The username of the person streaming.')
    parser.add_argument('--sessionId', required=True,
                        help='The unique identifier for the stream.')
    parser.add_argument('--killMessage', nargs='+',
                        help='Message to send to user whose stream is killed.')
    parser.add_argument('--notify', type=int,
                        help='Notification Agent ID number to Agent to send notification.')

    opts = parser.parse_args()

    if opts.killMessage:
        message = ' '.join(opts.killMessage)
    else:
        message = ''

    if opts.jbop == 'stream':
        terminate_session(opts.sessionId, message)
    elif opts.jbop == 'allStreams':
        streams = get_activity(opts.userId)
        for session_id in streams:
            terminate_session(session_id, message)

    if opts.notify:
        BODY_TEXT = BODY_TEXT.format(user=opts.username, message=message)
        send_notification(SUBJECT_TEXT, BODY_TEXT, opts.notify)
