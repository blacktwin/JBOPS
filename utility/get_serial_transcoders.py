#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Get a list of "Serial Transcoders".

Author: DirtyCajunRice
Requires: requests, plexapi, python3.6+
"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from past.utils import old_div
from requests import Session
from plexapi.server import CONFIG
from datetime import date, timedelta
from json.decoder import JSONDecodeError

TAUTULLI_URL = ''
TAUTULLI_API_KEY = ''

PAST_DAYS = 7
THRESHOLD_PERCENT = 50

# Do not edit past this line #

TAUTULLI_URL = TAUTULLI_URL or CONFIG.data['auth'].get('tautulli_baseurl')
TAUTULLI_API_KEY = TAUTULLI_API_KEY or CONFIG.data['auth'].get('tautulli_apikey')

TODAY = date.today()
START_DATE = TODAY - timedelta(days=PAST_DAYS)

SESSION = Session()
SESSION.params = {'apikey': TAUTULLI_API_KEY}
FORMATTED_URL = f'{TAUTULLI_URL}/api/v2'

PARAMS = {'cmd': 'get_history', 'grouping': 1, 'order_column': 'date', 'length': 1000}

REQUEST = None
try:
    REQUEST = SESSION.get(FORMATTED_URL, params=PARAMS).json()['response']['data']['data']
except JSONDecodeError:
    exit("Error talking to Tautulli API, please check your TAUTULLI_URL")

HISTORY = [play for play in REQUEST if date.fromtimestamp(play['started']) >= START_DATE]

USERS = {}
for play in HISTORY:
    if not USERS.get(play['user_id']):
        USERS.update(
            {
                play['user_id']: {
                    'direct play': 0,
                    'copy': 0,
                    'transcode': 0
                }
            }
        )
    USERS[play['user_id']][play['transcode_decision']] += 1

PARAMS = {'cmd': 'get_user', 'user_id': 0}
for user, counts in USERS.items():
    TOTAL_PLAYS = counts['transcode'] + counts['direct play'] + counts['copy']
    TRANSCODE_PERCENT = round(old_div(counts['transcode'] * 100, TOTAL_PLAYS), 2)
    if TRANSCODE_PERCENT >= THRESHOLD_PERCENT:
        PARAMS['user_id'] = user
        NAUGHTY = SESSION.get(FORMATTED_URL, params=PARAMS).json()['response']['data']
        print(f"{NAUGHTY['friendly_name']} is a serial transocde offender above the threshold at {TRANSCODE_PERCENT}%")
