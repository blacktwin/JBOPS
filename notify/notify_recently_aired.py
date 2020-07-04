#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description: Notify only if recently aired/released
Author: Blacktwin
Requires: requests

Enabling Scripts in Tautulli:
Tautulli > Settings > Notification Agents > Add a Notification Agent > Script

Configuration:
Tautulli > Settings > Notification Agents > New Script > Configuration:

 Script Name: notify_recently_aired.py
 Set Script Timeout: Default
 Description: Notify only if recently aired/released
 Save

Triggers:
Tautulli > Settings > Notification Agents > New Script > Triggers:

 Check: Recently Added
 Save

Conditions:
Tautulli > Settings > Notification Agents > New Script > Conditions:

 Set Conditions: [{condition} | {operator} | {value} ]
 Save

Script Arguments:
Tautulli > Settings > Notification Agents > New Script > Script Arguments:

 Select: Recently Added
 Arguments: {air_date} or {release_date} {rating_key}

 Save
 Close

Note:
    You'll need another notification agent to use for actually sending the notification.
    The notifier_id in the edit section will need to be this other notification agent you intend to use.
        It does not have to be an active notification agent, just setup.
"""
from __future__ import print_function
from __future__ import unicode_literals
import os
import sys
import requests
from datetime import date
from datetime import datetime

TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''
TAUTULLI_URL = os.getenv('TAUTULLI_URL', TAUTULLI_URL)
TAUTULLI_APIKEY = os.getenv('TAUTULLI_APIKEY', TAUTULLI_APIKEY)

# Edit
date_format = "%Y-%m-%d"
RECENT_DAYS = 3
NOTIFIER_ID = 34
# /Edit

air_date = sys.argv[1]
rating_key = int(sys.argv[2])

aired_date = datetime.strptime(air_date, date_format)
today = date.today()
delta = today - aired_date.date()


def notify_recently_added(rating_key, notifier_id):
    # Get the metadata for a media item.
    payload = {'apikey': TAUTULLI_APIKEY,
               'rating_key': rating_key,
               'notifier_id': notifier_id,
               'cmd': 'notify_recently_added'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        sys.stdout.write(response["response"]["message"])

    except Exception as e:
        sys.stderr.write("Tautulli API 'notify_recently_added' request failed: {0}.".format(e))
        pass


if delta.days < RECENT_DAYS:
    notify_recently_added(rating_key, NOTIFIER_ID)
else:
    print("Not recent enough, no notification to be sent.")
