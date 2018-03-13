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
        Condition {1} > Username > is not > UsernameToExclude
Taultulli > Settings > Notification Agents > New Script > Script Arguments:
        Playback Pause
        {session_key} {user} {title}
'''

#################### CONFIG ####################

PLEX_TOKEN = 'XXXXXXXXXXXXXXXXX'
PLEX_URL = 'http://127.0.0.1:3400'

TIMEOUT = 1200
INTERVAL = 20

KILL_MESSAGE = 'This stream has ended due to being paused for over 20 minutes.'

TAUTULLI_KILL_LOG = "Killed {user}'s {timeout}+ second paused stream of {title}."

############### DO NOT EDIT BELOW ###############

sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

sessionKey = sys.argv[1]
userName = sys.argv[2]
tTitle = sys.argv[3]

start = datetime.now()

countdown = 0
counter = TIMEOUT + INTERVAL + 100

while countdown < counter and countdown is not None:
    foundSession = False
    for session in plex.sessions():
        if session.sessionKey == int(sessionKey):
           foundSession = True
           username = session.usernames[0]
           title = (session.grandparentTitle + ' - ' if session.type == 'episode' else '') + session.title
           if session.players[0].state == 'paused':
              now = datetime.now()
              diff = now - start
              if diff.total_seconds() >= TIMEOUT:
                 session.stop(reason=KILL_MESSAGE)
                 print (TAUTULLI_KILL_LOG.format(user=username, timeout=TIMEOUT, title=title))
                 sys.exit(0)
              else:
                  sleep(INTERVAL)
                  counter = counter - INTERVAL
           elif session.players[0].state == 'playing' or session.players[0].state == 'buffering':
               print ("{} resumed the stream of {} so we killed the script.".format(username, title))
               sys.exit(0)
    if not foundSession:
           print ("Session key ({}) for user {} not found while playing {}. The player may have gone to a paused then stopped state.".format(sessionKey, userName, tTitle))
           sys.exit(0)
