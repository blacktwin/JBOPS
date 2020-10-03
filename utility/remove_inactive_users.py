#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unshare or Remove users who have been inactive for X days. Prints out last seen for all users.

Just run.

Comment out `remove_friend(username)` and `unshare(username)` to test.
"""
from sys import exit
from requests import Session
from datetime import datetime
from plexapi.server import PlexServer, CONFIG


# EDIT THESE SETTINGS #
PLEX_URL = ''
PLEX_TOKEN = ''
TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''

REMOVE_LIMIT = 14  # Days
UNSHARE_LIMIT = 15  # Days

USERNAME_IGNORE = ['user1', 'username2']
IGNORE_NEVER_SEEN = True
USE_USERLIST_LOG = True
DRY_RUN = True
# EDIT THESE SETTINGS #

# CODE BELOW #

PLEX_URL = PLEX_URL or CONFIG.data['auth'].get('server_baseurl')
PLEX_TOKEN = PLEX_TOKEN or CONFIG.data['auth'].get('server_token')
TAUTULLI_URL = TAUTULLI_URL or CONFIG.data['auth'].get('tautulli_baseurl')
TAUTULLI_APIKEY = TAUTULLI_APIKEY or CONFIG.data['auth'].get('tautulli_apikey')
USERNAME_IGNORE = [username.lower() for username in USERNAME_IGNORE]
SESSION = Session()
# Ignore verifying the SSL certificate
SESSION.verify = False  # '/path/to/certfile'
# If verify is set to a path to a directory,
# the directory must have been processed using the c_rehash utility supplied with OpenSSL.
if not SESSION.verify:
    # Disable the warning that the request is insecure, we know that...
    from urllib3 import disable_warnings
    from urllib3.exceptions import InsecureRequestWarning
    disable_warnings(InsecureRequestWarning)

SERVER = PlexServer(baseurl=PLEX_URL, token=PLEX_TOKEN, session=SESSION)
ACCOUNT = SERVER.myPlexAccount()
SECTIONS = [section.title for section in SERVER.library.sections()]
PLEX_USERS = {user.id: user.title for user in ACCOUNT.users()}
PLEX_USERS.update({int(ACCOUNT.id): ACCOUNT.title})
PLEX_NAMES = {user.title for user in ACCOUNT.users()}
PLEX_NAMES.update({ACCOUNT.title})
IGNORED_UIDS = [uid for uid, username in PLEX_USERS.items() if username.lower() in USERNAME_IGNORE]
IGNORED_UIDS.extend((int(ACCOUNT.id), 0))
# Get the Tautulli history.
PARAMS = {
    'cmd': 'get_users_table',
    'order_column': 'last_seen',
    'order_dir': 'asc',
    'length': 200,
    'apikey': TAUTULLI_APIKEY
}
TAUTULLI_USERS = []
try:
    GET = SESSION.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS).json()['response']['data']['data']
    for user in GET:
        if user['user_id'] in IGNORED_UIDS:
            continue
        elif IGNORE_NEVER_SEEN and not user['last_seen']:
            continue
        TAUTULLI_USERS.append(user)
except Exception as e:
    exit("Tautulli API 'get_users_table' request failed. Error: {}.".format(e))

UserList = open("Userlist.log", "r") # List of log lines
log_lines = UserList.read().split('\n')
UserList.close

def time_format(total_seconds):
    # Display user's last history entry
    days = total_seconds // 86400
    hours = (total_seconds - days * 86400) // 3600
    minutes = (total_seconds - days * 86400 - hours * 3600) // 60
    seconds = total_seconds - days * 86400 - hours * 3600 - minutes * 60
    result = ("{} day{}, ".format(days, "s" if days != 1 else "") if days else "") + \
             ("{} hour{}, ".format(hours, "s" if hours != 1 else "") if hours else "") + \
             ("{} minute{}, ".format(minutes, "s" if minutes != 1 else "") if minutes else "") + \
             ("{} second{}, ".format(seconds, "s" if seconds != 1 else "") if seconds else "")
    return result.strip().rstrip(',')


NOW = datetime.today()
for user in TAUTULLI_USERS:
    OUTPUT = []
    USERNAME = user['friendly_name']
    UID = user['user_id']
    if not user['last_seen']:
        TOTAL_SECONDS = None
        
        with open('UserList.log') as f:
            if USERNAME in f.read(): 
               for i, log in enumerate(log_lines):
                   if log != '': 
                        LIST_NAME = log.split(', ')[1]
                        if LIST_NAME not in PLEX_NAMES:
                           if DRY_RUN:
                              print (LIST_NAME + ' is in your UserList.log but not a friend on Plex, and would be removed from the log.')
                              del log_lines[i]
                           else:
                              del log_lines[i]
                              LIST_UPDATE = open("UserList.log", "w+")
                              for line in log_lines: 
                                  if line.rstrip(): LIST_UPDATE.write(line + "\n")
                              LIST_UPDATE.close()
                              print ('Removed ' + LIST_NAME + ' from UserList.log as user is no longer a friend on Plex.')

                   if USERNAME in log:
                        DATEADDED, sep, tail = log.partition(',')
                        DATESPLIT = DATEADDED.split("/")
                        from datetime import date
                        d0 = date(NOW.year, NOW.month, NOW.day)
                        d1 = date(int(DATESPLIT[0]), int(DATESPLIT[1]), int(DATESPLIT[2]))
                        DateDiff = d0 - d1
                        if int(DateDiff.days) > REMOVE_LIMIT: 
                           OUTPUT = '{} has never used the server, was added '.format(USERNAME) + str(DateDiff.days) + ' days ago'
                        else: 
                           OUTPUT = '{} has never used the server and was added '.format(USERNAME) + str(DateDiff.days) + ' days ago'
            else:
               OUTPUT = '{} has never used the server'.format(USERNAME)
                 

    else:
        TOTAL_SECONDS = int((NOW - datetime.fromtimestamp(user['last_seen'])).total_seconds())
        OUTPUT = '{} was last seen {} ago'.format(USERNAME, time_format(TOTAL_SECONDS))

    if UID not in PLEX_USERS.keys():
        print('{}, and exists in Tautulli but does not exist in Plex. Skipping.'.format(OUTPUT))
        continue

    if 'and was' in OUTPUT:
        print('{}. Skipping.'.format(OUTPUT))
        continue

    TOTAL_SECONDS = TOTAL_SECONDS or 86400 * UNSHARE_LIMIT
    if TOTAL_SECONDS >= (REMOVE_LIMIT * 86400):
        if DRY_RUN:
            print('{}, and would be removed.'.format(OUTPUT))
        else:
            print('{}, and has reached their shareless threshold. Removing.'.format(OUTPUT))
            ACCOUNT.removeFriend(PLEX_USERS[UID])
    elif TOTAL_SECONDS >= (UNSHARE_LIMIT * 86400):
        if DRY_RUN:
            print('{}, and would unshare libraries.'.format(OUTPUT))
        else:

            for server in ACCOUNT.user(PLEX_USERS[UID]).servers:
                if server.machineIdentifier == SERVER.machineIdentifier and server.sections():
                    print('{}, and has reached their inactivity limit. Unsharing.'.format(OUTPUT))
                    ACCOUNT.updateFriend(PLEX_USERS[UID], SERVER, SECTIONS, removeSections=True)
                else:
                    print("{}, has already been unshared, but has not reached their shareless threshold."
                          "Skipping.".format(OUTPUT))
