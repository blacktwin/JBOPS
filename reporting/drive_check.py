import psutil
import requests

# Drive letter to check if exists.
drive = 'F:'

disk = psutil.disk_partitions()

TAUTULLI_URL = 'http://localhost:8182/' # Your Tautulli URL
TAUTULLI_APIKEY = 'xxxxxx' # Enter your Tautulli API Key
NOTIFIER_LST = [10, 11] # The Tautulli notifier notifier id found here: https://github.com/drzoidberg33/plexpy/blob/master/plexpy/notifiers.py#L43
NOTIFY_SUBJECT = 'Tautulli' # The notification subject
NOTIFY_BODY = 'The Plex disk {0} was not found'.format(drive) # The notification body

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
