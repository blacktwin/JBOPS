#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description: Use conditions to kill a stream
Author: Blacktwin, Arcanemagus, Samwiseg0, JonnyWong16, DirtyCajunRice

Adding the script to Tautulli:
Tautulli > Settings > Notification Agents > Add a new notification agent >
 Script

Configuration:
Tautulli > Settings > Notification Agents > New Script > Configuration:

 Script Folder: /path/to/your/scripts
 Script File: ./kill_stream.py (Should be selectable in a dropdown list)
 Script Timeout: {timeout}
 Description: Kill stream(s)
 Save

Triggers:
Tautulli > Settings > Notification Agents > New Script > Triggers:

 Check: Playback Start and/or Playback Pause
 Save

Conditions:
Tautulli > Settings > Notification Agents > New Script > Conditions:

 Set Conditions: [{condition} | {operator} | {value} ]
 Save

Script Arguments:
Tautulli > Settings > Notification Agents > New Script > Script Arguments:

 Select: Playback Start, Playback Pause
 Arguments: --jbop SELECTOR --userId {user_id} --username {username}
            --sessionId {session_id} --notify notifierID
            --interval 30 --limit 1200
            --richMessage RICH_TYPE --serverName {server_name}
            --plexUrl {plex_url} --posterUrl {poster_url}
            --richColor '#E5A00D'
            --killMessage 'Your message here.'

 Save
 Close
"""


import os
import sys
import json
import time
import argparse
from datetime import datetime
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException


TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''
TAUTULLI_PUBLIC_URL = ''
TAUTULLI_URL = os.getenv('TAUTULLI_URL', TAUTULLI_URL)
TAUTULLI_PUBLIC_URL = os.getenv('TAUTULLI_PUBLIC_URL', TAUTULLI_PUBLIC_URL)
TAUTULLI_APIKEY = os.getenv('TAUTULLI_APIKEY', TAUTULLI_APIKEY)
TAUTULLI_ENCODING = os.getenv('TAUTULLI_ENCODING', 'UTF-8')
VERIFY_SSL = False

if TAUTULLI_PUBLIC_URL != '/':
    # Check to see if there is a public URL set in Tautulli
    TAUTULLI_LINK = TAUTULLI_PUBLIC_URL
else:
    TAUTULLI_LINK = TAUTULLI_URL

SUBJECT_TEXT = "Tautulli has killed a stream."
BODY_TEXT = "Killed session ID '{id}'. Reason: {message}"
BODY_TEXT_USER = "Killed {user}'s stream. Reason: {message}."


SELECTOR = ['stream', 'allStreams', 'paused']

RICH_TYPE = ['discord', 'slack']

TAUTULLI_ICON = 'https://github.com/Tautulli/Tautulli/raw/master/data/interfaces/default/images/logo-circle.png'


def utc_now_iso():
    """Get current time in ISO format"""
    utcnow = datetime.utcnow()

    return utcnow.isoformat()


def hex_to_int(value):
    """Convert hex value to integer"""
    try:
        return int(value, 16)
    except (ValueError, TypeError):
        return 0


def arg_decoding(arg):
    """Decode args, encode UTF-8"""
    return arg.decode(TAUTULLI_ENCODING).encode('UTF-8')


def debug_dump_vars():
    """Dump parameters for debug"""
    print('Tautulli URL - ' + TAUTULLI_URL)
    print('Tautulli Public URL - ' + TAUTULLI_PUBLIC_URL)
    print('Verify SSL - ' + str(VERIFY_SSL))
    print('Tautulli API key - ' + TAUTULLI_APIKEY[-4:]
          .rjust(len(TAUTULLI_APIKEY), "x"))


def get_all_streams(tautulli, user_id=None):
    """Get a list of all current streams.

    Parameters
    ----------
    user_id : int
        The ID of the user to grab sessions for.
    tautulli : obj
        Tautulli object.
    Returns
    -------
    objects
        The of stream objects.
    """
    sessions = tautulli.get_activity()['sessions']

    if user_id:
        streams = [Stream(session=s) for s in sessions if s['user_id'] == user_id]
    else:
        streams = [Stream(session=s) for s in sessions]

    return streams


def notify(all_opts, message, kill_type=None, stream=None, tautulli=None):
    """Decides which notifier type to use"""
    if all_opts.notify and all_opts.richMessage:
        rich_notify(all_opts.notify, all_opts.richMessage, all_opts.richColor, kill_type,
                    all_opts.serverName, all_opts.plexUrl, all_opts.posterUrl, message, stream, tautulli)
    elif all_opts.notify:
        basic_notify(all_opts.notify, all_opts.sessionId, all_opts.username, message, stream, tautulli)


def rich_notify(notifier_id, rich_type, color=None, kill_type=None, server_name=None,
                plex_url=None, poster_url=None, message=None, stream=None, tautulli=None):
    """Decides which rich notifier type to use. Set default values for empty variables

    Parameters
    ----------
    notifier_id : int
        The ID of the user to grab sessions for.
    rich_type : str
        Contains 'discord' or 'slack'.
    color : Union[int, str]
        Hex string or integer representation of color.
    kill_type : str
        The kill type used.
    server_name : str
        The name of the plex server.
    plex_url : str
        Plex media URL.
    poster_url : str
        The media poster URL.
    message : str
        Message sent to the client.
    stream : obj
        Stream object.
    tautulli : obj
        Tautulli object.
    """
    notification = Notification(notifier_id, None, None, tautulli, stream)
    # Initialize Variables
    title = ''
    footer = ''
    # Set a default server_name if none is provided
    if server_name is None:
        server_name = 'Plex Server'

    # Set a default color if none is provided
    if color is None:
        color = '#E5A00D'

    # Set a default plexUrl if none is provided
    if plex_url is None:
        plex_url = 'https://app.plex.tv'

    # Set a default posterUrl if none is provided
    if poster_url is None:
        poster_url = TAUTULLI_ICON

    # Set a default message if none is provided
    if message is None:
        message = 'The server owner has ended the stream.'

    if kill_type == 'Stream':
        title = "Killed {}'s stream.".format(stream.friendly_name)
        footer = '{} | Kill {}'.format(server_name, kill_type)

    elif kill_type == 'Paused':
        title = "Killed {}'s paused stream.".format(stream.friendly_name)
        footer = '{} | Kill {}'.format(server_name, kill_type)

    elif kill_type == 'All Streams':
        title = "Killed {}'s stream.".format(stream.friendly_name)
        footer = '{} | Kill {}'.format(server_name, kill_type)
        poster_url = TAUTULLI_ICON
        plex_url = 'https://app.plex.tv'

    if rich_type == 'discord':
        color = hex_to_int(color.lstrip('#'))
        notification.send_discord(title, color, poster_url, plex_url, message, footer)

    elif rich_type == 'slack':
        notification.send_slack(title, color, poster_url, plex_url, message, footer)


def basic_notify(notifier_id, session_id, username=None, message=None, stream=None, tautulli=None):
    """Basic notifier"""
    notification = Notification(notifier_id, SUBJECT_TEXT, BODY_TEXT, tautulli, stream)

    if username:
        body = BODY_TEXT_USER.format(user=username,
                                     message=message)
    else:
        body = BODY_TEXT.format(id=session_id, message=message)
    notification.send(SUBJECT_TEXT, body)


class Tautulli:
    def __init__(self, url, apikey, verify_ssl=False, debug=None):
        self.url = url
        self.apikey = apikey
        self.debug = debug

        self.session = Session()
        self.adapters = HTTPAdapter(max_retries=3,
                                    pool_connections=1,
                                    pool_maxsize=1,
                                    pool_block=True)
        self.session.mount('http://', self.adapters)
        self.session.mount('https://', self.adapters)

        # Ignore verifying the SSL certificate
        if verify_ssl is False:
            self.session.verify = False
            # Disable the warning that the request is insecure, we know that...
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _call_api(self, cmd, payload, method='GET'):
        payload['cmd'] = cmd
        payload['apikey'] = self.apikey

        try:
            response = self.session.request(method, self.url + '/api/v2', params=payload)
        except RequestException as e:
            print("Tautulli request failed for cmd '{}'. Invalid Tautulli URL? Error: {}".format(cmd, e))
            if self.debug:
                traceback.print_exc()
            return

        try:
            response_json = response.json()
        except ValueError:
            print(
                "Failed to parse json response for Tautulli API cmd '{}': {}"
                .format(cmd, response.content))
            return

        if response_json['response']['result'] == 'success':
            if self.debug:
                print("Successfully called Tautulli API cmd '{}'".format(cmd))
            return response_json['response']['data']
        else:
            error_msg = response_json['response']['message']
            print("Tautulli API cmd '{}' failed: {}".format(cmd, error_msg))
            return

    def get_activity(self, session_key=None, session_id=None):
        """Call Tautulli's get_activity api endpoint"""
        payload = {}

        if session_key:
            payload['session_key'] = session_key
        elif session_id:
            payload['session_id'] = session_id

        return self._call_api('get_activity', payload)

    def notify(self, notifier_id, subject, body):
        """Call Tautulli's notify api endpoint"""
        payload = {'notifier_id': notifier_id,
                   'subject': subject,
                   'body': body}

        return self._call_api('notify', payload)

    def terminate_session(self, session_key=None, session_id=None, message=''):
        """Call Tautulli's terminate_session api endpoint"""
        payload = {}

        if session_key:
            payload['session_key'] = session_key
        elif session_id:
            payload['session_id'] = session_id

        if message:
            payload['message'] = message

        return self._call_api('terminate_session', payload)


class Stream:
    def __init__(self, session_id=None, user_id=None, username=None, tautulli=None, session=None):
        self.state = None
        self.ip_address = None
        self.session_id = session_id
        self.user_id = user_id
        self.username = username
        self.session_exists = False
        self.tautulli = tautulli

        if session is not None:
            self._set_stream_attributes(session)

    def _set_stream_attributes(self, session):
        for k, v in session.items():
            setattr(self, k, v)

    def get_all_stream_info(self):
        """Get all stream info from Tautulli."""
        session = self.tautulli.get_activity(session_id=self.session_id)
        if session:
            self._set_stream_attributes(session)
            self.session_exists = True
        else:
            self.session_exists = False

    def terminate(self, message=''):
        """Calls Tautulli to terminate the session.

        Parameters
        ----------
        message : str
            The message to use if the stream is terminated.
        """
        self.tautulli.terminate_session(session_id=self.session_id, message=message)

    def terminate_long_pause(self, message, limit, interval):
        """Kills the session if it is paused for longer than <limit> seconds.

        Parameters
        ----------
        message : str
            The message to use if the stream is terminated.
        limit : int
            The number of seconds the session is allowed to remain paused before it
            is terminated.
        interval : int
            The amount of time to wait between checks of the session state.
        """
        start = datetime.now()
        checked_time = 0
        # Continue checking 2 intervals past the allowed limit in order to
        # account for system variances.
        check_limit = limit + (interval * 2)

        while checked_time < check_limit:
            self.get_all_stream_info()

            if self.session_exists is False:
                sys.stdout.write(
                    "Session '{}'  from user '{}' is no longer active "
                    .format(self.session_id, self.username) +
                    "on the server, stopping monitoring.\n")
                return False

            now = datetime.now()
            checked_time = (now - start).total_seconds()

            if self.state == 'paused':
                if checked_time >= limit:
                    self.terminate(message)
                    sys.stdout.write(
                        "Session '{}' from user '{}' has been killed.\n"
                        .format(self.session_id, self.username))
                    return True
                else:
                    time.sleep(interval)

            elif self.state == 'playing' or self.state == 'buffering':
                sys.stdout.write(
                    "Session '{}' from user '{}' has been resumed, "
                    .format(self.session_id, self.username) +
                    "stopping monitoring.\n")
                return False


class Notification:
    def __init__(self, notifier_id, subject, body, tautulli, stream):
        self.notifier_id = notifier_id
        self.subject = subject
        self.body = body

        self.tautulli = tautulli
        self.stream = stream

    def send(self, subject='', body=''):
        """Send to Tautulli notifier.

        Parameters
        ----------
        subject : str
            Subject of the message.
        body : str
            Body of the message.
        """
        subject = subject or self.subject
        body = body or self.body
        self.tautulli.notify(notifier_id=self.notifier_id, subject=subject, body=body)

    def send_discord(self, title, color, poster_url, plex_url, message, footer):
        """Build the Discord message.

        Parameters
        ----------
        title : str
            The title of the message.
        color : int
            The color of the message
        poster_url : str
            The media poster URL.
        plex_url : str
            Plex media URL.
        message : str
            Message sent to the player.
        footer : str
            Footer of the message.
        """
        discord_message = {
            "embeds": [
                {
                    "author": {
                        "icon_url": TAUTULLI_ICON,
                        "name": "Tautulli",
                        "url": TAUTULLI_LINK.rstrip('/')
                    },
                    "color": color,
                    "fields": [
                        {
                            "inline": True,
                            "name": "User",
                            "value": self.stream.friendly_name
                        },
                        {
                            "inline": True,
                            "name": "Session Key",
                            "value": self.stream.session_key
                        },
                        {
                            "inline": True,
                            "name": "Watching",
                            "value": self.stream.full_title
                        },
                        {
                            "inline": False,
                            "name": "Message Sent",
                            "value": message
                        }
                    ],
                    "thumbnail": {
                        "url": poster_url
                    },
                    "title": title,
                    "timestamp": utc_now_iso(),
                    "url": plex_url,
                    "footer": {
                        "text": footer
                    }

                }

            ],
        }

        discord_message = json.dumps(discord_message, sort_keys=True,
                                     separators=(',', ': '))
        self.send(body=discord_message)

    def send_slack(self, title, color, poster_url, plex_url, message, footer):
        """Build the Slack message.

        Parameters
        ----------
        title : str
            The title of the message.
        color : int
            The color of the message
        poster_url : str
            The media poster URL.
        plex_url : str
            Plex media URL.
        message : str
            Message sent to the player.
        footer : str
            Footer of the message.
        """
        slack_message = {
            "attachments": [
                {
                    "title": title,
                    "title_link": plex_url,
                    "author_icon": TAUTULLI_ICON,
                    "author_name": "Tautulli",
                    "author_link": TAUTULLI_LINK.rstrip('/'),
                    "color": color,
                    "fields": [
                        {
                            "title": "User",
                            "value": self.stream.friendly_name,
                            "short": True
                        },
                        {
                            "title": "Session Key",
                            "value": self.stream.session_key,
                            "short": True
                        },
                        {
                            "title": "Watching",
                            "value": self.stream.full_title,
                            "short": True
                        },
                        {
                            "title": "Message Sent",
                            "value": message,
                            "short": False
                        }
                    ],
                    "thumb_url": poster_url,
                    "footer": footer,
                    "ts": time.time()
                }

            ],
        }

        slack_message = json.dumps(slack_message, sort_keys=True,
                                   separators=(',', ': '))
        self.send(body=slack_message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Killing Plex streams from Tautulli.")
    parser.add_argument('--jbop', required=True, choices=SELECTOR,
                        help='Kill selector.\nChoices: (%(choices)s)')
    parser.add_argument('--userId', type=int,
                        help='The unique identifier for the user.')
    parser.add_argument('--username', type=arg_decoding,
                        help='The username of the person streaming.')
    parser.add_argument('--sessionId',
                        help='The unique identifier for the stream.')
    parser.add_argument('--notify', type=int,
                        help='Notification Agent ID number to Agent to ' +
                        'send notification.')
    parser.add_argument('--limit', type=int, default=(20 * 60),  # 20 minutes
                        help='The time session is allowed to remain paused.')
    parser.add_argument('--interval', type=int, default=30,
                        help='The seconds between paused session checks.')
    parser.add_argument('--killMessage', nargs='+', type=arg_decoding,
                        help='Message to send to user whose stream is killed.')
    parser.add_argument('--richMessage', type=arg_decoding, choices=RICH_TYPE,
                        help='Rich message type selector.\nChoices: (%(choices)s)')
    parser.add_argument('--serverName', type=arg_decoding,
                        help='Plex Server Name')
    parser.add_argument('--plexUrl', type=arg_decoding,
                        help='URL to plex media')
    parser.add_argument('--posterUrl', type=arg_decoding,
                        help='Poster URL of the media')
    parser.add_argument('--richColor', type=arg_decoding,
                        help='Color of the rich message')
    parser.add_argument("--debug", action='store_true',
                        help='Enable debug messages.')

    opts = parser.parse_args()

    if not opts.sessionId and opts.jbop != 'allStreams':
        sys.stderr.write("No sessionId provided! Is this synced content?\n")
        sys.exit(1)

    if opts.debug:
        # Import traceback to get more detailed information
        import traceback
        # Dump the ENVs passed from tautulli
        debug_dump_vars()

    # Create a Tautulli instance
    tautulli_server = Tautulli(TAUTULLI_URL.rstrip('/'), TAUTULLI_APIKEY, VERIFY_SSL, opts.debug)

    # Create initial Stream object with basic info
    tautulli_stream = Stream(opts.sessionId, opts.userId, opts.username, tautulli_server)

    # Only pull all stream info if using richMessage
    if opts.notify and opts.richMessage:
        tautulli_stream.get_all_stream_info()

    # Set a default message if none is provided
    if opts.killMessage:
        kill_message = ' '.join(opts.killMessage)
    else:
        kill_message = 'The server owner has ended the stream.'

    if opts.jbop == 'stream':
        tautulli_stream.terminate(kill_message)
        notify(opts, kill_message, 'Stream', tautulli_stream, tautulli_server)

    elif opts.jbop == 'allStreams':
        all_streams = get_all_streams(tautulli_server, opts.userId)
        for a_stream in all_streams:
            tautulli_server.terminate_session(session_id=a_stream.session_id, message=kill_message)
            notify(opts, kill_message, 'All Streams', a_stream, tautulli_server)

    elif opts.jbop == 'paused':
        killed_stream = tautulli_stream.terminate_long_pause(kill_message, opts.limit, opts.interval)
        if killed_stream:
            notify(opts, kill_message, 'Paused', tautulli_stream, tautulli_server)
