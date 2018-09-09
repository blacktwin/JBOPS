"""
Description: Use conditions to kill a stream
Author: Blacktwin, Arcanemagus, samwiseg00, WikiZell
Version: 2 (WikiZell)
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
            --killMessage 'Your message here.'

 Save
 Close
"""

import requests
import argparse
import sys
import os
from time import sleep
from datetime import datetime
#from configparser import ConfigParser
try:
    # Python 3.0+
    from configparser import SafeConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser

TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''
TAUTULLI_URL = os.getenv('TAUTULLI_URL', TAUTULLI_URL)
TAUTULLI_APIKEY = os.getenv('TAUTULLI_APIKEY', TAUTULLI_APIKEY)
TAUTULLI_ENCODING = os.getenv('TAUTULLI_ENCODING', 'UTF-8')

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

SELECTOR = ['stream', 'allStreams', 'paused', 'streamAllowed','configUser']

config = SafeConfigParser(allow_no_value=True)
configPath = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'userConfig.ini'

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
            sys.stdout.write("Successfully sent Tautulli notification.\n")
        else:
            raise Exception(response['response']['message'])
    except Exception as e:
        sys.stderr.write(
            "Tautulli API 'notify' request failed: {0}.\n".format(e))
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
            "Tautulli API 'get_activity' request failed: {0}.\n".format(e))
        return []


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

def get_user_names():
    """Get a list of all user and user ids.

    Returns
    -------
    json
        Get a list of all user and user ids.
    """
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_users'}

    try:
                                                  # api/v2?apikey=$apikey&cmd=$command
        req = sess.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = req.json()

        res_data = response['response']['data']
        #extra var
        for u in res_data:u['user_slot'] = '1'

        return res_data

    except Exception as e:
        sys.stderr.write(
            "Tautulli API 'get_user_names' request failed: {0}.\n".format(e))
        return []

def configUser():
    users = get_user_names()
    if not os.path.exists(configPath):
        #Config file not exists -> Create and populate with basic info
        for u in users:
          config[str(u['user_id'])] = u #{'username': u['username'], 'user_id': str(u['user_id']), 'user_slot': '1', 'email': u['email'] }
          with open(configPath, 'w') as fp:
               config.write(fp)
    else:
     #Update if new user_slot
     config.read(configPath)
     sections = []
     for section in config.sections():sections.append(section)
     s = set(sections)
     for u in users:
         if not str(u['user_id']) in s:
             config[str(u['user_id'])] = u
             with open(configPath, 'w') as fp:
                  config.write(fp)
    config.read(configPath)
    pass

    sections = []
    for section in config.sections():sections.append(str(section))

    serverSections = []
    for uss in users:serverSections.append(str(uss['user_id']))

    s = set(serverSections)
    for sectionToRemove in sections:
        if not str(sectionToRemove) in s:
           #section to remove
            removeSection(sectionToRemove)

def removeSection(sectionToRemove):
    config.read(configPath)
    config.remove_section(sectionToRemove)
    with open(configPath, 'w') as fp:
         config.write(fp)

def check_session(streamCount, userId, session_id, notifier=None, username=None):

    configUser()

    config.read(configPath)
    try:
        slotsAllowed = config.get(userId,'user_slot')
    except:
        slotsAllowed = "1"
    pass

    if int(streamCount) > int(slotsAllowed):
        #kill stream: too many concurrent streams
        message = 'No stream slot available! You can use a total of '+ slotsAllowed +' stream slots.'
        sys.stdout.write('Detected: too many concurrent streams\n')
        sys.stdout.write('Stream Count: '+streamCount+' Streams Allowed: '+slotsAllowed+'\n')
        sys.stdout.write('Executing terminate_session..\n')
        terminate_session(session_id, message, notifier=None, username=None)
    else:
        sys.stdout.write('Concurrent stream status: '+streamCount+' of '+slotsAllowed+'\n')
    return None

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
                "Successfully killed Plex session: {0}.\n".format(session_id))
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


def terminate_long_pause(session_id, message, limit, interval, notify=None, username=None):
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
                        terminate_session(session_id, message, notify, username)
                        return
                    else:
                        sleep(interval)
                elif state == 'playing' or state == 'buffering':
                    sys.stdout.write(
                        "Session '{}' has resumed, ".format(session_id) +
                        "stopping monitoring.\n")
                    return
        if not found_session:
            sys.stdout.write(
                "Session '{}' is no longer active ".format(session_id) +
                "on the server, stopping monitoring.\n")
            return


def arg_decoding(arg):
    return arg.decode(TAUTULLI_ENCODING).encode('UTF-8')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Killing Plex streams from Tautulli.")
    parser.add_argument('--jbop', required=True, choices=SELECTOR,
                        help='Kill selector.\nChoices: (%(choices)s)')
    parser.add_argument('--userId',
                        help='The unique identifier for the user.')
    parser.add_argument('--username', type=arg_decoding,
                        help='The username of the person streaming.')
    parser.add_argument('--sessionId',
                        help='The unique identifier for the stream.')
    parser.add_argument('--notify', type=int,
                        help='Notification Agent ID number to Agent to send ' +
                             'notification.')
    parser.add_argument('--limit', type=int, default=(20 * 60),  # 20 minutes
                        help='The time session is allowed to remain paused.')
    parser.add_argument('--interval', type=int, default=30,
                        help='The seconds between paused session checks.')
    parser.add_argument('--killMessage', nargs='+', type=arg_decoding,
                        help='Message to send to user whose stream is killed.')
    parser.add_argument('--streamCount',
                        help='Concurrent streams count.')

    opts = parser.parse_args()

    if opts.jbop == 'configUser':
        configUser()
        sys.stderr.write("User config done....ok\n")
        sys.stderr.write("Config path: "+configPath+"\n")
        sys.exit(0)

    if not opts.sessionId and opts.jbop != 'allStreams':
        sys.stderr.write("No sessionId provided! Is this synced content?\n")
        sys.exit(1)

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
                             opts.interval, opts.notify, opts.username)
    elif opts.jbop == 'streamAllowed':
        check_session(opts.streamCount, opts.userId, opts.sessionId, opts.notify, opts.username)
