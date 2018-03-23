# -*- coding: utf-8 -*-

'''
wait_kill_pause_notify_main.py & wait_kill_pause_notify_sub.py should be in the same directory.
wait_kill_pause_notify_main.py executes sub_script wait_kill_pause_notify_sub.py.

Tautulli will timeout wait_kill_pause_notify_main.py after 30 seconds (default)
    but wait_kill_pause_notify_sub.py will continue.

wait_kill_pause_notify_sub will check if the stream's session_id is still paused or if playing as restarted.
If playback is restarted then wait_kill_pause_notify_sub will stop and delete itself.
If stream remains paused then it will be killed and wait_kill_pause_notify_sub will stop.
Set TIMEOUT to max time before killing stream
Set INTERVAL to how often you want to check the stream status
'''

import sys
from time import sleep
from wait_kill_pause_notify_main import kill_stream, check_session

sessionKey =  int(sys.argv[1])
timeout = int(sys.argv[2])
interval = int(sys.argv[3])

x = 0

try:
    print('Executing sub script.')
    while x < timeout and x is not None:
        sleep(interval)
        if kill_stream(check_session(sessionKey), interval, timeout) is not None:
            x += kill_stream(check_session(sessionKey), interval, timeout)
        else:
            print('Exiting sub script.')
            exit(0)
    print('Sub script initiating kill.')
    kill_stream(check_session(sessionKey), timeout, timeout)

except Exception as e:
    print('Error: {}'.format(e))

