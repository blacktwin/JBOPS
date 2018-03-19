'''
Refresh the next episode of show once current episode is watched.
Check Tautulli's Watched Percent in Tautulli > Settings > General

1. Tautulli > Settings > Notification Agents > Scripts > Bell icon:
    [X] Notify on watched
2. Tautulli > Settings > Notification Agents > Scripts > Gear icon:
    Enter the "Script folder" where you save the script.
    Watched: refresh_next_episode.py
    Save
3. Tautulli > Settings > Notifications > Script > Script Arguments:
    {show_name} {episode_num00} {season_num00}

'''

import sys
from plexapi.server import PlexServer
# pip install plexapi


baseurl = 'http://localhost:32400'
token = 'XXXXXX'  # Plex Token
plex = PlexServer(baseurl, token)

show_name = sys.argv[1]
next_ep_num = int(sys.argv[2])
season_num = int(sys.argv[3])
TV_LIBRARY = 'My TV Shows' # Name of your TV Shows library

current_season = season_num - 1

# Get all seasons from Show
all_seasons = plex.library.section(TV_LIBRARY).get(show_name).seasons()

try:
    # Get all episodes from current season of Show
    all_eps = all_seasons[current_season].episodes()
    # Refresh the next episode
    all_eps[next_ep_num].refresh()
except IndexError:
    try:
        # End of season go to next season
        all_eps = all_seasons[season_num].episodes()
        # Refresh the next season's first episode
        all_eps[0].refresh()
    except IndexError:
        print('End of series')
