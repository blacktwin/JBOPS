import psutil
import requests
import urllib

# Drive letter to check if exists.
drive = 'D:'

disk = psutil.disk_partitions()

PLEXPY_URL = 'http://localhost:8181/' # Your PlexPy URL
PLEXPY_APIKEY = '#####' # Enter your PlexPy API Key
AGENT_ID = 10 # The PlexPy notifier agent id found here: https://github.com/drzoidberg33/plexpy/blob/master/plexpy/notifiers.py#L43
NOTIFY_SUBJECT = 'PlexPy' # The notification subject
NOTIFY_BODY = 'The Plex disk {0} was not found'.format(drive) # The notification body

disk_check = [True for i in disk if drive in i.mountpoint]

if not disk_check:
    # Send notification to PlexPy using the API
    data = {'apikey': PLEXPY_APIKEY,
            'cmd': 'notify',
            'agent_id': int(AGENT_ID),
            'subject': NOTIFY_SUBJECT,
            'body': NOTIFY_BODY}

    url = PLEXPY_URL + 'api/v2?' + urllib.urlencode(data)
    r = requests.post(url)
else:
    pass
