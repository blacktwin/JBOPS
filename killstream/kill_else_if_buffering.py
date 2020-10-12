#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
If server admin stream is experiencing buffering and there are concurrent transcode streams from
another user, kill concurrent transcode stream that has the lowest percent complete. Message in
kill stream will list why it was killed ('Server Admin's stream take priority and this user has X
concurrent streams'). Message will also include an approximation of when the other concurrent stream
will finish, stream that is closest to finish will be used.

Tautulli > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on buffer warning

Tautulli > Settings > Notification Agents > Scripts > Gear icon:
        Buffer Warnings: kill_else_if_buffering.py

"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from builtins import str
from past.utils import old_div
import requests
from operator import itemgetter
import unicodedata
from plexapi.server import PlexServer


# ## EDIT THESE SETTINGS ##
PLEX_TOKEN = 'xxxx'
PLEX_URL = 'http://localhost:32400'

DEFAULT_REASON = 'Server Admin\'s stream takes priority and {user}(you) has {x} concurrent streams.' \
                 ' {user}\'s stream of {video} is {time}% complete. Should be finished in {comp} minutes. ' \
                 'Try again then.'

ADMIN_USER = ('Admin')  # Additional usernames can be added ('Admin', 'user2')
# ##

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)


def kill_session(sess_key, message):
    for session in plex.sessions():
        # Check for users stream
        username = session.usernames[0]
        if session.sessionKey == sess_key:
            title = str(session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
            title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').translate(None, "'")
            session.stop(reason=message)
            print('Terminated {user}\'s stream of {title} to prioritize admin stream.'.format(user=username,
                                                                                              title=title))


def add_to_dictlist(d, key, val):
    if key not in d:
        d[key] = [val]
    else:
        d[key].append(val)


def main():
    user_dict = {}

    for session in plex.sessions():
        if session.transcodeSessions:
            trans_dec = session.transcodeSessions[0].videoDecision
            username = session.usernames[0]
            if trans_dec == 'transcode' and username not in ADMIN_USER:
                sess_key = session.sessionKey
                percent_comp = int((float(session.viewOffset) / float(session.duration)) * 100)
                time_to_comp = old_div(old_div(int(int(session.duration) - int(session.viewOffset)), 1000), 60)
                title = str(session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
                title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').translate(None, "'")
                add_to_dictlist(user_dict, username, [sess_key, percent_comp, title, username, time_to_comp])

    # Remove users with only 1 stream. Targeting users with multiple concurrent streams
    filtered_dict = {key: value for key, value in user_dict.items()
                     if len(value) != 1}

    # Find who to kill and who will be finishing first.
    if filtered_dict:
        for users in filtered_dict.values():
            to_kill = min(users, key=itemgetter(1))
            to_finish = max(users, key=itemgetter(1))

        MESSAGE = DEFAULT_REASON.format(user=to_finish[3], x=len(filtered_dict.values()[0]),
                                        video=to_finish[2], time=to_finish[1], comp=to_finish[4])

        print(MESSAGE)
        kill_session(to_kill[0], MESSAGE)


if __name__ == '__main__':
    main()
