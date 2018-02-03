'''
Use PlexPy to pull last IP address from user and add to List of IP addresses and networks that are allowed without auth in Plex.

optional arguments:
  -h, --help            show this help message and exit
  -u  [ ...], --users  [ ...]
                        Space separated list of case sensitive names to process. Allowed names are:
                        (choices: {List of all Plex users} )
                        (default: None)
  -c [], --clear []     Clear List of IP addresses and networks that are allowed without auth in Plex:
                        (choices: None)
                        (default: None)

List of IP addresses is cleared before adding new IPs
'''

import requests
import ConfigParser
import io
import argparse
import sys

# Load the configuration file
with open("../config.ini") as f:
    real_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=False)
config.readfp(io.BytesIO(real_config))

PLEXPY_APIKEY=config.get('plexpy-data', 'PLEXPY_APIKEY')
PLEXPY_URL=config.get('plexpy-data', 'PLEXPY_URL')
PLEX_TOKEN=config.get('plex-data', 'PLEX_TOKEN')
PLEX_URL=config.get('plex-data', 'PLEX_URL')


def get_get_history(user_id):
    # Get the user history from PlexPy
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_history',
               'user_id': user_id,
               'length': 1}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return [d['ip_address'] for d in res_data]

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_get_history' request failed: {0}.".format(e))


def get_get_user_names(username):
    # Get the user names from PlexPy
    payload = {'apikey': PLEXPY_APIKEY,
               'cmd': 'get_user_names'}

    try:
        r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']
        if username:
            return [d['user_id'] for d in res_data if d['friendly_name'] in username]
        else:
            return [d['friendly_name'] for d in res_data]

    except Exception as e:
        sys.stderr.write("PlexPy API 'get_get_user_names' request failed: {0}.".format(e))


def add_auth_bypass(net_str):
    headers = {"X-Plex-Token": PLEX_TOKEN}
    params = {"allowedNetworks": net_str}
    requests.put("{}/:/prefs".format(PLEX_URL), headers=headers, params=params)


if __name__ == '__main__':

    user_lst = get_get_user_names('')
    parser = argparse.ArgumentParser(description="Use PlexPy to pull last IP address from user and add to List of "
                                                 "IP addresses and networks that are allowed without auth in Plex.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-u', '--users', nargs='+', type=str, choices=user_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s) \n(default: %(default)s)')
    parser.add_argument('-c', '--clear', nargs='?',default=None, metavar='',
                        help='Clear List of IP addresses and networks that are allowed without auth in Plex: \n'
                             '(default: %(default)s)')

    opts = parser.parse_args()

    if opts.clear and opts.users is None:
        print('Clearing List of IP addresses and networks that are allowed without auth in Plex.')
        add_auth_bypass('')
    elif opts.clear and len(opts.users) == 1:
        print('Clearing List of IP addresses and networks that are allowed without auth in Plex.')
        add_auth_bypass('')
        user_id = get_get_user_names(opts.users)
        user_ip = get_get_history(user_id)
        print('Adding {} to List of IP addresses and networks that are allowed without auth in Plex.'
              .format(''.join(user_ip)))
        add_auth_bypass(user_ip)
    elif opts.clear and len(opts.users) > 1:
        print('Clearing List of IP addresses and networks that are allowed without auth in Plex.')
        add_auth_bypass('')
        userid_lst = [get_get_user_names(user_names) for user_names in opts.users]
        userip_lst = [get_get_history(user_id) for user_id in userid_lst]
        flat_list = [item for sublist in userip_lst for item in sublist]
        print('Adding {} to List of IP addresses and networks that are allowed without auth in Plex.'
              .format(', '.join(flat_list)))
        add_auth_bypass(', '.join(flat_list))
    else:
        print('I don\'t know what else you want.')
