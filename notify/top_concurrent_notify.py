#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Description: Check Tautulli's most concurrent from home stats against current concurrent count.
             If greater notify using an existing agent.
Author: Blacktwin
Requires: requests

Enabling Scripts in Tautulli:
Tautulli > Settings > Notification Agents > Add a Notification Agent > Script

Configuration:
Tautulli > Settings > Notification Agents > New Script > Configuration:

 Script Name: Most Concurrent Record
 Set Script Timeout: {timeout}
 Description: New Most Concurrent Record
 Save

Triggers:
Tautulli > Settings > Notification Agents > New Script > Triggers:

 Check: Playback Start
 Save

Conditions:
Tautulli > Settings > Notification Agents > New Script > Conditions:

 Set Conditions: [{condition} | {operator} | {value} ]
 Save

Script Arguments:
Tautulli > Settings > Notification Agents > New Script > Script Arguments:

 Select: Playback Start
 Arguments: --streams {streams} --notifier notifierID

*notifierID of the existing agent you want to use to send notification.


 Save
 Close

 Example:


"""
from __future__ import unicode_literals

import os
import sys
import requests
import argparse


# ### EDIT SETTINGS ###

TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''
TAUTULLI_URL = os.getenv('TAUTULLI_URL', TAUTULLI_URL)
TAUTULLI_APIKEY = os.getenv('TAUTULLI_APIKEY', TAUTULLI_APIKEY)
VERIFY_SSL = False


SUBJECT = 'New Record for Most Concurrent Streams!'
BODY = 'New server record for most concurrent streams is now {}.'

# ## CODE BELOW ##


def get_home_stats():
    # Get the homepage watch statistics.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_home_stats'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']
        most_concurrents = [rows for rows in res_data if rows['stat_id'] == 'most_concurrent']
        concurrent_rows = most_concurrents[0]['rows']
        return concurrent_rows

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_home_stats' request failed: {0}.".format(e))
        

def notify(notifier_id, subject, body):
    """Call Tautulli's notify api endpoint"""
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'notify',
               'notifier_id': notifier_id,
               'subject': subject,
               'body': body}
    
    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']
        return res_data

    except Exception as e:
        sys.stderr.write("Tautulli API 'notify' request failed: {0}.".format(e))
        


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Notification of new most concurrent streams count.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--streams', required=True, type=int,
                        help='Current streams count from Tautulli.')
    parser.add_argument('--notifier', required=True,
                        help='Tautulli notification ID to send notification to.')
    
    opts = parser.parse_args()
    
    most_concurrent = get_home_stats()
    for result in most_concurrent:
        if result['title'] == 'Concurrent Streams':
            if opts.streams > result['count']:
                notify(notifier_id=opts.notifier, subject=SUBJECT, body=BODY.format(opts.streams))