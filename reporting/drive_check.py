import psutil
import requests

# Drive letter to check if exists.
drive = 'F:'

disk = psutil.disk_partitions()

PLEXPY_URL = 'http://localhost:8182/' # Your PlexPy URL
PLEXPY_APIKEY = 'xxxxxx' # Enter your PlexPy API Key
AGENT_LST = [10, 11] # The PlexPy notifier agent id found here: https://github.com/drzoidberg33/plexpy/blob/master/plexpy/notifiers.py#L43
NOTIFY_SUBJECT = 'PlexPy' # The notification subject
NOTIFY_BODY = 'The Plex disk {0} was not found'.format(drive) # The notification body

disk_check = [True for i in disk if drive in i.mountpoint]

if not disk_check:
    # Send the notification through PlexPy
    payload = {'apikey': PLEXPY_APIKEY,
            'cmd': 'notify',
            'subject': NOTIFY_SUBJECT,
            'body': NOTIFY_BODY}

    for agent in AGENT_LST:
        payload['agent_id'] = agent
        requests.post(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
else:
    pass
