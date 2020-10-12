#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Enable or disable all users remote access to Tautulli.

Author: DirtyCajunRice
Requires: requests, python3.6+
"""
from __future__ import print_function
from __future__ import unicode_literals

from requests import Session
from json.decoder import JSONDecodeError

ENABLE_REMOTE_ACCESS = True

TAUTULLI_URL = ''
TAUTULLI_API_KEY = ''

# Do not edit past this line #
session = Session()
session.params = {'apikey': TAUTULLI_API_KEY}
formatted_url = f'{TAUTULLI_URL}/api/v2'

request = session.get(formatted_url, params={'cmd': 'get_users'})

tautulli_users = None
try:
    tautulli_users = request.json()['response']['data']
except JSONDecodeError:
    exit("Error talking to Tautulli API, please check your TAUTULLI_URL")

allow_guest = 1 if ENABLE_REMOTE_ACCESS else 0
string_representation = 'Enabled' if ENABLE_REMOTE_ACCESS else 'Disabled'

users_to_change = [user for user in tautulli_users if user['allow_guest'] != allow_guest]

if users_to_change:
    for user in users_to_change:
        # Redefine ALL params because of Tautulli edit_user API bug
        params = {
            'cmd': 'edit_user',
            'user_id': user['user_id'],
            'friendly_name': user['friendly_name'],
            'custom_thumb': user['custom_thumb'],
            'keep_history': user['keep_history'],
            'allow_guest': allow_guest
        }
        changed_user = session.get(formatted_url, params=params)
        print(f"{string_representation} guest access for {user['friendly_name']}")
else:
    print(f'No users to {string_representation.lower()[:-1]}')
