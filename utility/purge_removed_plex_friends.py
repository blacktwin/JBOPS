#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Purge Tautulli users that no longer exist as a friend in Plex.

Author: DirtyCajunRice
Requires: requests, plexapi, python3.6+
"""
from __future__ import print_function
from __future__ import unicode_literals

from requests import Session
from plexapi.server import CONFIG
from json.decoder import JSONDecodeError
from plexapi.myplex import MyPlexAccount

TAUTULLI_URL = ''
TAUTULLI_API_KEY = ''

PLEX_USERNAME = ''
PLEX_PASSWORD = ''

# Do you want to back up the database before deleting?
BACKUP_DB = True

# Do not edit past this line #

# Grab config vars if not set in script
TAUTULLI_URL = TAUTULLI_URL or CONFIG.data['auth'].get('tautulli_baseurl')
TAUTULLI_API_KEY = TAUTULLI_API_KEY or CONFIG.data['auth'].get('tautulli_apikey')
PLEX_USERNAME = PLEX_USERNAME or CONFIG.data['auth'].get('myplex_username')
PLEX_PASSWORD = PLEX_PASSWORD or CONFIG.data['auth'].get('myplex_password')

account = MyPlexAccount(PLEX_USERNAME, PLEX_PASSWORD)

session = Session()
session.params = {'apikey': TAUTULLI_API_KEY}
formatted_url = f'{TAUTULLI_URL}/api/v2'

request = session.get(formatted_url, params={'cmd': 'get_user_names'})

tautulli_users = None
try:
    tautulli_users = request.json()['response']['data']
except JSONDecodeError:
    exit("Error talking to Tautulli API, please check your TAUTULLI_URL")

plex_friend_ids = [friend.id for friend in account.users()]
plex_friend_ids.extend((0, int(account.id)))
removed_users = [user for user in tautulli_users if user['user_id'] not in plex_friend_ids]

if BACKUP_DB:
    backup = session.get(formatted_url, params={'cmd': 'backup_db'})

if removed_users:
    for user in removed_users:
        removed_user = session.get(formatted_url, params={'cmd': 'delete_user', 'user_id': user['user_id']})
        print(f"Removed {user['friendly_name']} from Tautulli")
else:
    print('No users to remove')
