"""
Description: Kill paused sessions if paused for X amount of time.
Author: samwiseg00
Requires: requests, plexapi

Enabling Scripts in Tautulli:
Taultulli > Settings > Notification Agents > Add a Notification Agent > Script

Configuration:
Taultulli > Settings > Notification Agents > New Script > Configuration:

 Script Name: wait_kill_notify.py
 Set Script Timeout: 0
 Description: Killing long pauses
 Save

Triggers:
Taultulli > Settings > Notification Agents > New Script > Triggers:

 Check: Playback Pause
 Save

Conditions:
Taultulli > Settings > Notification Agents > New Script > Conditions:

 Set Conditions: Condition {1} | Username | is not | UsernameToExclude
 Save

Script Arguments:
Taultulli > Settings > Notification Agents > New Script > Script Arguments:

 Select: Playback Pause
 Arguments: {session_key} {user} {title} TIMEOUT INTERVAL

 Save
 Close

Example:
 {session_key} {user} {title} 1200 20
 This will tell the script to kill the stream after 20 minutes and check every 20 seconds

"""

import os
import sys
from time import sleep
from datetime import datetime
from plexapi.server import PlexServer
import requests

PLEX_FALLBACK_URL = 'http://127.0.0.1:32400'
PLEX_FALLBACK_TOKEN = ''
PLEX_URL = os.getenv('PLEX_URL', PLEX_FALLBACK_URL)
PLEX_TOKEN = os.getenv('PLEX_TOKEN', PLEX_FALLBACK_TOKEN)

PLEX_OVERRIDE_URL = ''
PLEX_OVERRIDE_TOKEN = ''

if PLEX_OVERRIDE_URL:
    PLEX_URL = PLEX_OVERRIDE_URL
if PLEX_OVERRIDE_TOKEN:
    PLEX_TOKEN = PLEX_OVERRIDE_TOKEN


sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

sessionKey = sys.argv[1]
username = sys.argv[2]
streamTitle = sys.argv[3]
timeout = int(sys.argv[4])
interval = int(sys.argv[5])

seconds = int(timeout)

minutes, seconds = divmod(seconds, 60)
hours, minutes = divmod(minutes, 60)

periods = [('hours', hours), ('minutes', minutes), ('seconds', seconds)]
time_string = ', '.join('{} {}'.format(value, name)
                        for name, value in periods
                        if value)
start = datetime.now()

countdown = 0
counter = timeout + interval + 100

while countdown < counter and countdown is not None:

    foundSession = False

    for session in plex.sessions():

        if session.sessionKey == int(sessionKey):
            foundSession = True
            state = session.players[0].state

            if state == 'paused':
                now = datetime.now()
                diff = now - start

                if diff.total_seconds() >= timeout:
                    session.stop(reason="This stream has ended due to being paused for over {}.".format(time_string))
                    print ("Killed {}'s {} paused stream of {}.".format(username, time_string, streamTitle))
                    sys.exit(0)

                else:
                    sleep(interval)
                    counter = counter - interval

            elif state == 'playing' or state == 'buffering':
                print ("{} resumed the stream of {} so we killed the script.".format(username, streamTitle))
                sys.exit(0)

    if not foundSession:
        print ("Session key ({}) for user {} not found while playing {}. "
               "The player may have gone to a paused then stopped state.".format(sessionKey, username, streamTitle))
        sys.exit(0)
