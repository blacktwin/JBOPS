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
 Arguments: --ratingKey {rating_key} --userTo "Username2" "Username3" --userFrom {username}

 Save
 Close

 Example:
    Set in Tautulli in script notification agent or run manually

    plex_api_share.py --userFrom USER1 --userTo USER2 --libraries Movies
       - Synced watch status of {title from library} to {USER2}'s account.

    plex_api_share.py --userFrom USER1 --userTo USER2 USER3 --allLibraries
       - Synced watch status of {title from library} to {USER2 or USER3}'s account.

    Excluding;
    --libraries becomes excluded if --allLibraries is set
    sync_watch_status.py --userFrom USER1 --userTo USER2 --allLibraries --libraries Movies
       - Shared [all libraries but Movies] with USER.

"""
import requests
import argparse
import os
from plexapi.server import PlexServer

PLEX_OVERRIDE_URL = ''
PLEX_URL = PLEX_OVERRIDE_URL or os.getenv('PLEX_URL')

PLEX_OVERRIDE_TOKEN = ''
PLEX_TOKEN = PLEX_OVERRIDE_TOKEN or os.getenv('PLEX_TOKEN')


sess = requests.Session()
sess.verify = False
plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=sess)

sections_lst = [x.title for x in plex.library.sections()]
user_lst = [x.title for x in plex.myPlexAccount().users()]
# Adding admin account name to list
user_lst.append(plex.myPlexAccount().title)

def get_account(user):
    if user == plex.myPlexAccount().title:
        server = plex
    else:
        # Access Plex User's Account
        userAccount = plex.myPlexAccount().user(user)
        token = userAccount.get_token(plex.machineIdentifier)
        server = PlexServer(PLEX_URL, token)
    return server


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
    requiredNamed.add_argument('--userFrom', nargs=None, choices=user_lst, metavar='username', required=True,
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s)')
    requiredNamed.add_argument('--userTo', nargs='*', choices=user_lst, metavar='usernames', required=True,
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '(choices: %(choices)s)')

    opts = parser.parse_args()
    # print(opts)

    # Create Sync-From user account
    plexFrom = get_account(opts.userFrom)

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

    # Go through list of users
    for user in opts.userTo:
        # Create Sync-To user account
        plexTo = get_account(user)
        if libraries:
            # Go through Libraries
            for library in libraries:
                try:
                    print('Checking library: {}'.format(library))
                    # Check library for watched items
                    section = plexFrom.library.section(library).search(unwatched=False)
                    for item in section:
                        title = item.title.encode('utf-8')
                        # Check movie media type
                        if item.type == 'movie':
                            plexTo.fetchItem(item.key).markWatched()
                            print('Synced watch status of {} to {}\'s account.'.format(title, user))
                        # Check show media type
                        elif item.type == 'show':
                            # If one episode is watched, series is flagged as watched
                            for child in item.episodes():
                                # Check each episode
                                if child.isWatched:
                                    ep_title = child.title.encode('utf-8')
                                    plexTo.fetchItem(child.key).markWatched()
                                    print('Synced watch status of {} - {} to {}\'s account.'
                                          .format(title, ep_title, user))
                except Exception as e:
                    if str(e).startswith('Unknown'):
                        print('Library ({}) does not have a watch status.'.format(library))
                    elif str(e).startswith('Invalid'):
                        print('Library ({}) not shared to user: {}.'.format(library, opts.userFrom))
                    elif str(e).startswith('(404)'):
                        print('Library ({}) not shared to user: {}.'.format(library, user))
                    else:
                        print(e)
                    pass
        # Check rating key from Tautulli
        elif opts.ratingKey:
            item = plexTo.fetchItem(opts.ratingKey)
            title = item.title.encode('utf-8')
            print('Syncing watch status of {} to {}\'s account.'.format(title, user))
            item.markWatched()
        else:
            print('No libraries or rating key provided.')
