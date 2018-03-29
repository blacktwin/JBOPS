"""
Description: Use conditions to kill a stream
Author: Blacktwin
Requires: requests

Enabling Scripts in Tautulli:
Taultulli > Settings > Notification Agents > Add a Notification Agent > Script

Configuration:
Taultulli > Settings > Notification Agents > New Script > Configuration:

 Script Name: kill_stream
 Set Script Timeout: {timeout}
 Description: Kill stream
 Save

Triggers:
Taultulli > Settings > Notification Agents > New Script > Triggers:

 Check: {trigger}
 Save

Conditions:
Taultulli > Settings > Notification Agents > New Script > Conditions:

 Set Conditions: [{condition} | {operator} | {value} ]
 Save

Script Arguments:
Taultulli > Settings > Notification Agents > New Script > Script Arguments:

 Select: Playback Start, Playback Pause
 Arguments: {session_id}

 Save
 Close

 Example:
     Kill transcodes:
        Set Trigger: Playback Start
        Set Conditions: [ {Transcode Decision} | {is} | {transcode} ]

     Kill paused transcodes:
        Set Trigger: Playback Paused
        Set Conditions: [ {Transcode Decision} | {is} | {transcode} ]

     IP Whitelist:
        Set Trigger: Playback Start
        Set Conditions: [ {IP Address} | {is not} | {192.168.0.100 or 192.168.0.101} ]

     Kill by platform:
        Set Trigger: Playback Start
        Set Conditions: [ {Platform} | {is} | {Roku or Android} ]

     Kill transcode by library:
        Set Trigger: Playback Start
        Set Conditions: [ {Transcode Decision} | {is} | {transcode} ]
                        [ {Library Name} | {is} | {4K Movies} ]

     Kill transcode by original resolution:
        Set Trigger: Playback Start
        Set Conditions: [ {Transcode Decision} | {is} | {transcode} ]
                        [ {Video Resolution} | {is} | {1080 or 720}]

     Kill transcode by bitrate:
        Set Trigger: Playback Start
        Set Conditions: [ {Transcode Decision} | {is} | {transcode} ]
                        [ {Bitrate} | {is greater than} | {4000} ]

     Kill by hours of the day:
        Set Trigger: Playback Start
        Set Conditions: [ {Timestamp} | {begins with} | {09 or 10} ]
        # Killing any streams from 9am to 11am

     Kill non local streams:
        Set Trigger: Playback Start
        Set Conditions: [ {Stream location} | {is} | {wan} ]
        or
        Set Conditions: [ {Stream location} | {is not} | {lan} ]

"""

import requests
import sys
import os

TAUTULLI_FALLBACK_URL = ''
TAUTULLI_FALLBACK_APIKEY = ''
TAUTULLI_URL = os.getenv('TAUTULLI_URL', TAUTULLI_FALLBACK_URL)
TAUTULLI_APIKEY = os.getenv('TAUTULLI_APIKEY', TAUTULLI_FALLBACK_APIKEY)

TAUTULLI_OVERRIDE_URL = ''
TAUTULLI_OVERRIDE_API = ''

if TAUTULLI_OVERRIDE_URL:
    TAUTULLI_URL = TAUTULLI_OVERRIDE_URL
if TAUTULLI_OVERRIDE_API:
    TAUTULLI_APIKEY = TAUTULLI_OVERRIDE_API

MESSAGE = 'Your stream was terminated for "reasons"'

session_id = str(sys.argv[1])

payload = {'apikey': TAUTULLI_APIKEY,
           'cmd': 'terminate_session',
           'session_id': session_id,
           'message': MESSAGE}

requests.post(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
