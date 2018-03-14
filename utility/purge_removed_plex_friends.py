import requests
from plexapi.myplex import MyPlexAccount

TAUTULLI_BASE_URL = '192.168.1.100:8181'
TAUTULLI_API_KEY = 'asd8a9sd8789asd87f9aasdf'

PLEX_USERNAME = 'someuser'
PLEX_PASSWORD = 'somepassword'

# Do not edit past this line #
account = MyPlexAccount(PLEX_USERNAME, PLEX_PASSWORD)

payload = {'apikey': TAUTULLI_API_KEY, 'cmd': 'get_user_names'}
tautulli_users = requests.get('http://{}/api/v2'
                              .format(TAUTULLI_BASE_URL), params=payload).json()['response']['data']

plex_friend_ids = [friend.id for friend in account.users()]
tautulli_user_ids = [user['user_id'] for user in tautulli_users]

removed_user_ids = [user_id for user_id in tautulli_user_ids if user_id not in plex_friend_ids]

if removed_user_ids:
    payload['cmd'] = 'delete_user'

    for user_id in removed_user_ids:
        payload['user_id'] = user_id
        remove_user = requests.get('http://{}/api/v2'.format(TAUTULLI_BASE_URL), params=payload)
