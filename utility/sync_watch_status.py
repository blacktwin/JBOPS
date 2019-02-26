#!/usr/bin/env python
"""
Description: Sync the watch status from one user to another. Either by user or user/libraries
Author: Blacktwin
Requires: requests, plexapi, argparse

Enabling Scripts in Tautulli:
Taultulli > Settings > Notification Agents > Add a Notification Agent > Script

Configuration:
Taultulli > Settings > Notification Agents > New Script > Configuration:

 Script Name: sync_watch_status.py
 Set Script Timeout: default
 Description: Sync watch status
 Save

Triggers:
Taultulli > Settings > Notification Agents > New Script > Triggers:

 Check: Notify on Watched
 Save

Conditions:
Taultulli > Settings > Notification Agents > New Script > Conditions:

 Set Conditions: [{username} | {is} | {user_to_sync_from} ]
 Save

Script Arguments:
Taultulli > Settings > Notification Agents > New Script > Script Arguments:

 Select: Notify on Watched
 Arguments: --ratingKey {rating_key} --userTo "Username2=Server1" "Username3=Server1" --userFrom {username}={server_name}

 Save
 Close

 Example:
    Set in Tautulli in script notification agent or run manually

    sync_watch_status.py --userFrom USER1=Server --userTo USER2=Server --libraries Movies
       - Synced watch status of {title from library} to {USER2}'s account.

    sync_watch_status.py --userFrom USER1=Server --userTo USER2=Server USER3=Server --allLibraries
       - Synced watch status of {title from library} to {USER2 or USER3}'s account.

    Excluding;
    --libraries becomes excluded if --allLibraries is set
    sync_watch_status.py --userFrom USER1=Server --userTo USER2=Server --allLibraries --libraries Movies
       - Shared [all libraries but Movies] with USER.

"""
import sys
import requests
import argparse
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer, CONFIG


# Using CONFIG file
PLEX_TOKEN = ''
TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''

if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token', '')
if not TAUTULLI_URL:
    TAUTULLI_URL = CONFIG.data['auth'].get('tautulli_baseurl')
if not TAUTULLI_APIKEY:
    TAUTULLI_APIKEY = CONFIG.data['auth'].get('tautulli_apikey')


sess = requests.Session()
# Ignore verifying the SSL certificate
sess.verify = False  # '/path/to/certfile'
# If verify is set to a path to a directory,
# the directory must have been processed using the c_rehash utility supplied
# with OpenSSL.
if sess.verify is False:
    # Disable the warning that the request is insecure, we know that...
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

account = MyPlexAccount(PLEX_TOKEN)

# todo-me This is cleaned up. Should only connect to servers that are selected
sections_lst = []
user_servers = {}
admin_servers = {}
server_users = account.users()
user_server_dict = {'data': {}}
user_data = user_server_dict['data']

# Finding and connecting to owned servers.
print('Connecting to admin owned servers.')
for resource in account.resources():
    if 'server' in [resource.provides] and resource.ownerid == 0:
        server_connect = resource.connect()
        admin_servers[resource.name] = server_connect
        # Pull section names to check against
        server_sections = [section.title for section in server_connect.library.sections()]
        sections_lst += server_sections

sections_lst = list(set(sections_lst))

# Add admin account
user_data[account.title] = {'account': account,
                            'servers': admin_servers}

# Finding what user has access to which admin owned servers
for user in server_users:
    for server in user.servers:
        if admin_servers.get(server.name):
            user_servers[server.name] = admin_servers.get(server.name)
            if not user_data.get(user.title):
                user_data[user.title] =  {'account': user,
                                          'servers': user_servers}

# todo-me Add Tautulli history for syncing watch statuses from Tautulli to Plex
def get_history(user_id, media_type):
    # Get the user history from Tautulli.
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_history',
               'user_id': user_id,
               'media_type': media_type}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']['data']

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_history' request failed: {0}.".format(e))


def get_account(user, server):
    """
    Parameters
    ----------
    user: str
        User's name
    server: str
        Server's name

    Returns
    -------
        User server class

    """
    print('Checking {} on {}'.format(user, server))
    if user_server_dict['data'][user]['servers'].get(server):
        user_server = user_server_dict['data'][user]['servers'].get(server)
        baseurl = user_server._baseurl.split('.')
        url = ''.join([baseurl[0].replace('-', '.'),
                       baseurl[-1].replace('direct', '')])
        if user == MyPlexAccount(PLEX_TOKEN).title:
            token = PLEX_TOKEN
        else:
            userAccount = user_server.myPlexAccount().user(user)
            token = userAccount.get_token(user_server.machineIdentifier)
        account = PlexServer(baseurl=url, token=token, session=sess)
        return account
    else:
        print('{} is not shared to {}'.format(user, server))
        exit()


def mark_watached(sectionFrom, accountTo, userTo):
    """
    Parameters
    ----------
    sectionFrom: class
        Section class of sync from server
    accountTo: class
        User's server class of sync to user

    """
    # Check sections for watched items
    print('Marking watched...')
    sectionTo = accountTo.library.section(sectionFrom.title)
    for item in sectionFrom.search(unwatched=False):
        title = item.title.encode('utf-8')
        try:
            # Check movie media type
            if item.type == 'movie':
                watch_check = sectionTo.get(item.title)
                fetch_check = sectionTo.fetchItem(watch_check.key)
                if not fetch_check.isWatched:
                    fetch_check.markWatched()
                    print('Synced watch status of {} to {}\'s account.'.format(title, userTo))
            # Check show media type
            elif item.type == 'show':
                for episode in sectionFrom.searchEpisodes(unwatched=False, title=title):
                    ep_title = episode.title.encode('utf-8')
                    watch_check = sectionTo.get(item.title)
                    fetch_check = sectionTo.fetchItem(watch_check.key)
                    if not fetch_check.isWatched:
                        fetch_check.markWatched()
                        print('Synced watch status of {} - {} to {}\'s account.'.format(title, ep_title, userTo))
        except Exception:
            pass


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Sync watch status from one user to others.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    requiredNamed = parser.add_argument_group('required named arguments')
    parser.add_argument('--libraries', nargs='*', choices=sections_lst, metavar='library',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s)')
    parser.add_argument('--allLibraries', action='store_true',
                        help='Select all libraries.')
    parser.add_argument('--ratingKey', nargs=1,
                        help='Rating key of item whose watch status is to be synced.')
    requiredNamed.add_argument('--userFrom', metavar='user=server', required=True,
                               type=lambda kv: kv.split("="),
                               help='Select user and server to sync from')
    requiredNamed.add_argument('--userTo', nargs='*', metavar='user=server', required=True,
                               type=lambda kv: kv.split("="),
                               help='Select user and server to sync to.')

    opts = parser.parse_args()

    # Defining libraries
    libraries = ''
    if opts.allLibraries and not opts.libraries:
        libraries = sections_lst
    elif not opts.allLibraries and opts.libraries:
        libraries = opts.libraries
    elif opts.allLibraries and opts.libraries:
        # If allLibraries is used then any libraries listed will be excluded
        for library in opts.libraries:
            sections_lst.remove(library)
            libraries = sections_lst

    # Create Sync-From user account
    plexFrom = get_account(opts.userFrom[0], opts.userFrom[1])

    # Go through list of users
    for user in opts.userTo:
        plexTo = get_account(user[0], user[1])
        if libraries:
            # Go through Libraries
            for library in libraries:
                try:
                    print('Checking library: {}'.format(library))
                    # Check library for watched items
                    section = plexFrom.library.section(library)
                    mark_watached(section, plexTo, user[0])
                except Exception as e:
                    if str(e).startswith('Unknown'):
                        print('Library ({}) does not have a watch status.'.format(library))
                    elif str(e).startswith('(404)'):
                        print('Library ({}) not shared to user: {}.'.format(library, user))
                    else:
                        print(e)
                    pass
        # Check rating key from Tautulli
        elif opts.ratingKey:
            for key in opts.ratingKey:
                item = plexTo.fetchItem(int(key))
                title = item.title.encode('utf-8')
                print('Syncing watch status of {} to {}\'s account.'.format(title, user[0]))
                item.markWatched()
        else:
            print('No libraries or rating key provided.')
