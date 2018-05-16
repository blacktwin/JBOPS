import psutil
import requests
import ConfigParser
import io
import urllib

# Drive letter to check if exists.
drive = 'D:'

disk = psutil.disk_partitions()

TAUTULLI_APIKEY = ''  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8183/'  # Your Tautulli URL
NOTIFIER_LST = [10, 11] # The Tautulli notifier notifier id found here: https://github.com/drzoidberg33/plexpy/blob/master/plexpy/notifiers.py#L43
NOTIFY_SUBJECT = 'Tautulli' # The notification subject
NOTIFY_BODY = 'The Plex disk {0} was not found'.format(drive) # The notification body

## DO NOT EDIT
config_exists = os.path.exists("../config.ini")
if config_exists:
    # Load the configuration file
    with open("../config.ini") as f:
        real_config = f.read()
        config = ConfigParser.RawConfigParser(allow_no_value=False)
        config.readfp(io.BytesIO(real_config))

        TAUTULLI_APIKEY=config.get('tautulli-data', 'TAUTULLI_APIKEY')
        TAUTULLI_URL=config.get('tautulli-data', 'TAUTULLI_URL')
##/DO NOT EDIT

disk_check = [True for i in disk if drive in i.mountpoint]

if not disk_check:
    # Send the notification through Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
            'cmd': 'notify',
            'subject': NOTIFY_SUBJECT,
            'body': NOTIFY_BODY}

    for notifier in NOTIFIER_LST:
        payload['notifier_id'] = notifier
        requests.post(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
else:
    pass
