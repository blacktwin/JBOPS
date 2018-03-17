import os
import sys
import requests
from time import sleep
from datetime import datetime
from plexapi.server import PlexServer
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning # This is for python 2.7 may need to be removed for python3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning) # This is for python 2.7 may need to be removed for python3

'''
Taultulli > Settings > Notification Agents > Add a Notification Agent > Script

Taultulli > Settings > Notification Agents > New Script > Configuration:
        Script File > Playback Pause: v
        Script Timeout > 0
Taultulli > Settings > Notification Agents > New Script > Triggers:
        [X] Notify on Playback Pause
Taultulli > Settings > Notification Agents > New Script > Conditions:
        Set any conditions that you would like ie. exlude users
        Condition {1} | Username | is not | UsernameToExclude
Taultulli > Settings > Notification Agents > New Script > Script Arguments:
        Playback Pause
        {session_key} {user} {title} TIMEOUT INTERVAL  <- In Seconds

        Example:
        {session_key} {user} {title} 1200 20
        This will tell the script to kill the stream after 20 minutes and check every 20 seconds
'''

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

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

           if session.players[0].state == 'paused':
              now = datetime.now()
              diff = now - start

              if diff.total_seconds() >= timeout:
                 session.stop(reason="This stream has ended due to being paused for over {}.".format(time_string))
                 print ("Killed {}'s {} paused stream of {}.".format(username, time_string, streamTitle))
                 sys.exit(0)

              else:
                  sleep(interval)
                  counter = counter - interval

           elif session.players[0].state == 'playing' or session.players[0].state == 'buffering':
               print ("{} resumed the stream of {} so we killed the script.".format(username, streamTitle))
               sys.exit(0)

    if not foundSession:
           print ("Session key ({}) for user {} not found while playing {}. The player may have gone to a paused then stopped state.".format(sessionKey, username, streamTitle))
           sys.exit(0)
