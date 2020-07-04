#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description: Limiting Plex users by plays, watches, or total time from Tautulli.
Author: Blacktwin, Arcanemagus
Requires: requests

Adding the script to Tautulli:
Taultulli > Settings > Notification Agents > Add a new notification agent >
 Script

Configuration:
Taultulli > Settings > Notification Agents > New Script > Configuration:

 Script Folder: /path/to/your/scripts
 Script File: ./limiterr.py (Should be selectable in a dropdown list)
 Script Timeout: {timeout}
 Description: Kill stream(s)
 Save

Triggers:
Taultulli > Settings > Notification Agents > New Script > Triggers:

 Check: Playback Start
 Save

Conditions:
Taultulli > Settings > Notification Agents > New Script > Conditions:

 Set Conditions: [{condition} | {operator} | {value} ]
 Save

Script Arguments:
Taultulli > Settings > Notification Agents > New Script > Script Arguments:

 Select: Playback Start, Playback Pause
 Arguments: --jbop SELECTOR --username {username}
            --sessionId {session_id} --notify notifierID
            --grandparent_rating_key {grandparent_rating_key}
            --limit plays=3 --delay 60
            --killMessage 'Your message here.'
            --today

 Save
 Close
"""
from __future__ import print_function
from __future__ import unicode_literals

from builtins import range
import requests
import argparse
from datetime import datetime, timedelta
import sys
import os
from plexapi.server import PlexServer
from time import time as ttime
from time import sleep

TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''
PLEX_URL = ''
PLEX_TOKEN = ''

# Environmental Variables
PLEX_URL = os.getenv('PLEX_URL', PLEX_URL)
PLEX_TOKEN = os.getenv('PLEX_TOKEN', PLEX_TOKEN)
TAUTULLI_URL = os.getenv('TAUTULLI_URL', TAUTULLI_URL)
TAUTULLI_APIKEY = os.getenv('TAUTULLI_APIKEY', TAUTULLI_APIKEY)
TAUTULLI_ENCODING = os.getenv('TAUTULLI_ENCODING', 'UTF-8')

# Using CONFIG file
# from plexapi.server import CONFIG
# PLEX_URL = CONFIG.data['auth'].get('server_baseurl', PLEX_URL)
# PLEX_TOKEN = CONFIG.data['auth'].get('server_token', PLEX_TOKEN)
# TAUTULLI_URL = CONFIG.data['auth'].get('tautulli_baseurl', TAUTULLI_URL)
# TAUTULLI_APIKEY = CONFIG.data['auth'].get('tautulli_apikey', TAUTULLI_APIKEY)

SUBJECT_TEXT = "Tautulli has killed a stream."
BODY_TEXT = "Killed session ID '{id}'. Reason: {message}"
BODY_TEXT_USER = "Killed {user}'s stream. Reason: {message}."
LIMIT_MESSAGE = 'Are you still watching or are you asleep? ' \
                'If not please wait ~{delay} seconds and try again.'

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

plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)
lib_dict = {x.title: x.key for x in plex.library.sections()}


SELECTOR = ['watch', 'plays', 'time', 'limit']
TODAY = datetime.now()
unix_time = int(ttime())


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
        req = sess.post(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = req.json()

        if response['response']['result'] == 'success':
            sys.stdout.write("Successfully sent Tautulli notification.\n")
        else:
            raise Exception(response['response']['message'])
    except Exception as e:
        sys.stderr.write(
            "Tautulli API 'notify' request failed: {0}.\n".format(e))
        return None


def get_activity(session_id=None):
    """Get the current activity on the PMS.

    Returns
    -------
    list
        The current active sessions on the Plex server.
    """
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_activity'}
    if session_id:
        payload['session_id'] = session_id

    try:
        req = sess.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = req.json()

        if session_id:
            res_data = response['response']['data']
        else:
            res_data = response['response']['data']['sessions']
        return res_data

    except Exception as e:
        sys.stderr.write(
            "Tautulli API 'get_activity' request failed: {0}.\n".format(e))
        pass


def get_history(username, start_date=None, section_id=None):
    """Get the Tautulli history.

    Parameters
    ----------
    username : str
        The username to gather history from.

    Optional
    ----------
    start_date : list ["YYYY-MM-DD", ...]
        The date in history to search.
    section_id : int
        The libraries numeric identifier

    Returns
    -------
    dict
        The total number of watches, plays, or total playtime.
    """
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'user': username}

    if start_date:
        payload['start_date'] = start_date

    if section_id:
        payload['section_id '] = section_id

    try:
        req = sess.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = req.json()

        res_data = response['response']['data']
        return res_data

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))


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


def arg_decoding(arg):
    return arg.decode(TAUTULLI_ENCODING).encode('UTF-8')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Limiting Plex users by plays, watches, or total time from Tautulli.")
    parser.add_argument('--jbop', required=True, choices=SELECTOR,
                        help='Limit selector.\nChoices: (%(choices)s)')
    parser.add_argument('--username', required=True,
                        help='The username of the person streaming.')
    parser.add_argument('--sessionId', required=True,
                        help='The unique identifier for the stream.')
    parser.add_argument('--notify', type=int,
                        help='Notification Agent ID number to Agent to send '
                             'notification.')
    parser.add_argument('--limit', action='append', type=lambda kv: kv.split("="),
                        help='The limit related to the limit selector chosen.')
    parser.add_argument('--grandparent_rating_key', type=int,
                        help='The unique identifier for the TV show or artist.')
    parser.add_argument('--delay', type=int, default=60,
                        help='The seconds to wait in order to deem user is active.')
    parser.add_argument('--killMessage', nargs='+',
                        help='Message to send to user whose stream is killed.')
    parser.add_argument('--section', default=False, choices=lib_dict.keys(), metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s)')
    parser.add_argument('--days', type=int, default=0, nargs='?',
                        help='Search history limit. \n'
                             'Default: %(default)s day(s) (today).')
    parser.add_argument('--duration', type=int, default=0,
                        help='Duration of item that triggered script agent.')

    opts = parser.parse_args()

    history_lst = []
    total_limit = 0
    total_jbop = 0
    duration = 0
    dates = []
    delta = timedelta(days=opts.days)

    for i in range(delta.days + 1):
        day = TODAY + timedelta(days=-i)
        dates.append(day.strftime('%Y-%m-%d'))

    if opts.limit:
        limit = dict(opts.limit)

        for key, value in limit.items():
            if key == 'days':
                total_limit += int(value) * (24 * 60 * 60)
            elif key == 'hours':
                total_limit += int(value) * (60 * 60)
            elif key == 'minutes':
                total_limit += int(value) * 60
            elif key == 'plays':
                total_limit = int(value)

    if not opts.sessionId:
        sys.stderr.write("No sessionId provided! Is this synced content?\n")
        sys.exit(1)

    if opts.duration:
        # If duration is used convert to seconds from minutes
        duration = opts.duration * 60

    if opts.killMessage:
        message = ' '.join(opts.killMessage)
    else:
        message = ''

    for date in dates:
        if opts.section:
            section_id = lib_dict[opts.section]
            history = get_history(username=opts.username, section_id=section_id, start_date=date)
        else:
            history = get_history(username=opts.username, start_date=date)
        history_lst.append(history)
        
    if opts.jbop == 'watch':
        total_jbop = sum([data['watched_status'] for history in history_lst for data in history['data']])
    if opts.jbop == 'time':
        total_jbop = sum([data['duration'] for history in history_lst for data in history['data']])
    if opts.jbop == 'plays':
        total_jbop = sum([history['recordsFiltered'] for history in history_lst])

    if total_jbop:
        if total_jbop > total_limit:
            print('Total {} ({}) is greater than limit ({}).'
                  .format(opts.jbop, total_jbop, total_limit))
            terminate_session(opts.sessionId, message, opts.notify, opts.username)
        elif (duration + total_jbop) > total_limit:
            interval = 60
            start = 0
            while (start + total_jbop) < total_limit:
                if get_activity(opts.sessionId):
                    sleep(interval)
                    start += interval
                else:
                    print('Session; {} has been dropped. Stopping monitoring of stream.'.format(opts.sessionId))
                    exit()

            print('Total {} ({} + current item duration {}) is greater than limit ({}).'
                  .format(opts.jbop, total_jbop, duration, total_limit))
            terminate_session(opts.sessionId, message, opts.notify, opts.username)
        else:
            if duration:
                print('Total {} ({} + current item duration {}) is less than limit ({}).'
                      .format(opts.jbop, total_jbop, duration, total_limit))
            else:
                print('Total {} ({}) is less than limit ({}).'
                      .format(opts.jbop, total_jbop, total_limit))
    # todo-me need more flexibility for pulling history
    # limit work requires gp_rating_key only? Needs more options.
    if opts.jbop == 'limit' and opts.grandparent_rating_key:
        ep_watched = []
        stopped_time = []
        for date in dates:
            history_lst.append(get_history(username=opts.username, start_date=date))
        # If message is not already defined use default message
        if not message:
            message = LIMIT_MESSAGE.format(delay=opts.delay)
        for history in history_lst:
            ep_watched += [data['watched_status'] for data in history['data']
                          if data['grandparent_rating_key'] == opts.grandparent_rating_key and
                          data['watched_status'] == 1]
            
            stopped_time += [data['stopped'] for data in history['data']
                            if data['grandparent_rating_key'] == opts.grandparent_rating_key and
                            data['watched_status'] == 1]
            
        # If show has no history for date range start at 0.
        if not ep_watched:
            ep_watched = 0
        else:
            ep_watched = sum(ep_watched)

        # If show episode have not been stopped (completed?) then use current time.
        # Last stopped time is needed to test against auto play timer
        if not stopped_time:
            stopped_time = unix_time
        else:
            stopped_time = stopped_time[0]

        if abs(stopped_time - unix_time) > opts.delay:
            print('{} is awake!'.format(opts.username))
            sys.exit(1)

        if ep_watched >= total_limit:
            print("{}'s limit is {} and has watched {} episodes of this show.".format(
                opts.username, total_limit, ep_watched))
            terminate_session(opts.sessionId, message, opts.notify, opts.username)
        else:
            print("{}'s limit is {} but has only watched {} episodes of this show.".format(
                opts.username, total_limit, ep_watched))
