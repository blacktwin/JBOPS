'''
Use Tautulli to pull last IP address from user and add to List of IP addresses and networks that are allowed without auth in Plex.

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
import argparse
import sys


## EDIT THESE SETTINGS ##
PLEX_TOKEN = 'xxxx'
PLEX_URL = 'http://localhost:32400'
TAUTULLI_APIKEY = 'xxxx'  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL


def get_history(user_id):
    # Get the user history from Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'user_id': user_id,
               'length': 1}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return [d['ip_address'] for d in res_data]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))


def get_user_names(username):
    # Get the user names from Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_user_names'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']
        if username:
            return [d['user_id'] for d in res_data if d['friendly_name'] in username]
        else:
            return [d['friendly_name'] for d in res_data]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_user_names' request failed: {0}.".format(e))


def add_auth_bypass(net_str):
    headers = {"X-Plex-Token": PLEX_TOKEN}
    params = {"allowedNetworks": net_str}
    requests.put("{}/:/prefs".format(PLEX_URL), headers=headers, params=params)


if __name__ == '__main__':

    user_lst = get_user_names('')
    parser = argparse.ArgumentParser(description="Use Tautulli to pull last IP address from user and add to List of "
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
        user_id = get_user_names(opts.users)
        user_ip = get_history(user_id)
        print('Adding {} to List of IP addresses and networks that are allowed without auth in Plex.'
              .format(''.join(user_ip)))
        add_auth_bypass(user_ip)
    elif opts.clear and len(opts.users) > 1:
        print('Clearing List of IP addresses and networks that are allowed without auth in Plex.')
        add_auth_bypass('')
        userid_lst = [get_user_names(user_names) for user_names in opts.users]
        userip_lst = [get_history(user_id) for user_id in userid_lst]
        flat_list = [item for sublist in userip_lst for item in sublist]
        print('Adding {} to List of IP addresses and networks that are allowed without auth in Plex.'
              .format(', '.join(flat_list)))
        add_auth_bypass(', '.join(flat_list))
    else:
        print('I don\'t know what else you want.')
