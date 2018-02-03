import psutil
import requests
import ConfigParser
import io
import urllib

# Drive letter to check if exists.
drive = 'D:'

disk = psutil.disk_partitions()

# Load the configuration file
with open("../config.ini") as f:
    real_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=False)
config.readfp(io.BytesIO(real_config))

PLEXPY_APIKEY=config.get('plexpy-data', 'PLEXPY_APIKEY')
PLEXPY_URL=config.get('plexpy-data', 'PLEXPY_URL')
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
