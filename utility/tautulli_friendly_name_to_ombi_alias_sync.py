#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Sync Tautulli friendly names with Ombi aliases (Tautulli as master).

Author: DirtyCajunRice
Requires: requests, python3.6+
"""
from __future__ import print_function
from __future__ import unicode_literals
from requests import Session
from plexapi.server import CONFIG
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

OMBI_BASEURL = ''
OMBI_APIKEY = ''

TAUTULLI_BASEURL = ''
TAUTULLI_APIKEY = ''

# Dont Edit Below #
TAUTULLI_BASEURL = TAUTULLI_BASEURL or CONFIG.data['auth'].get('tautulli_baseurl')
TAUTULLI_APIKEY = TAUTULLI_APIKEY or CONFIG.data['auth'].get('tautulli_apikey')
OMBI_BASEURL = OMBI_BASEURL or CONFIG.data['auth'].get('ombi_baseurl')
OMBI_APIKEY = OMBI_APIKEY or CONFIG.data['auth'].get('ombi_apikey')

disable_warnings(InsecureRequestWarning)
SESSION = Session()
SESSION.verify = False

HEADERS = {'apiKey': OMBI_APIKEY}
PARAMS = {'apikey': TAUTULLI_APIKEY, 'cmd': 'get_users'}

TAUTULLI_USERS = SESSION.get('{}/api/v2'.format(TAUTULLI_BASEURL.rstrip('/')), params=PARAMS).json()['response']['data']
TAUTULLI_MAPPED = {user['username']: user['friendly_name'] for user in TAUTULLI_USERS
                   if user['user_id'] != 0 and user['friendly_name']}
OMBI_USERS = SESSION.get('{}/api/v1/Identity/Users'.format(OMBI_BASEURL.rstrip('/')), headers=HEADERS).json()

for user in OMBI_USERS:
    if user['userName'] in TAUTULLI_MAPPED and user['alias'] != TAUTULLI_MAPPED[user['userName']]:
        print("{}'s alias in Tautulli ({}) is being updated in Ombi from {}".format(
            user['userName'], TAUTULLI_MAPPED[user['userName']], user['alias'] or 'empty'
        ))
        user['alias'] = TAUTULLI_MAPPED[user['userName']]
        put = SESSION.put('{}/api/v1/Identity'.format(OMBI_BASEURL.rstrip('/')), json=user, headers=HEADERS)
        if put.status_code != 200:
            print('Error updating {}'.format(user['userName']))
