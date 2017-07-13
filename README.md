# JBOPS - Just a Bunch Of Plex Scripts

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=4J6RPWZ9J9YML) 

Scripts pulled from my gist profile. https://gist.github.com/blacktwin

### PlexPy Script Arguments:
`-sn {show_name} -ena {episode_name} -ssn {season_num00} -enu {episode_num00} -srv {server_name} -med {media_type} -pos {poster_url} -tt {title} -sum {summary} -lbn {library_name} -grk {grandparent_rating_key} -ip {ip_address} -us {user} -uid {user_id} -pf {platform} -pl {player} -da {datestamp} -ti {timestamp} -purl {plex_url}`

#### Enabling Scripts:

In the Notification Agents in the Settings menu. Click the Scripts gear. Your scripts location will be there. Can't remember if it's set automatically or not. If not, then set it where you'll keep your scripts. Scroll down to option you want to use and select the script from the drop down menu. Save. Click the Bell next to Scripts and enable Recently Added. Then click Notifications. Scroll down to Scripts. Enter in the Script Arguments found in the .py script. Save.


## Scripts List

| Category | File | Description |
| :--- | :--- | :--- |
|[Fun](../tree/master/fun "Fun Fun Fun Fun")|||
||[aired_today_playlist](../blob/master/fun/aired_today_playlist.py) | Create a Plex Playlist with what was aired on this today's month-day, sort by oldest first. If Playlist from yesterday exists delete and create today's. If today's Playlist exists exit.|
||[plexapi_haiku](../blob/master/fun/plexapi_haiku.py)| Create a hiaku from titles found in Plex.|
|[Kill stream](../tree/master/killstream "Kill Kill Kill")|||
||[create_wait_kill_all](../blob/master/killstream/create_wait_kill_all.py)|Receive session_key from PlexPy when paused. Use session_id to create sub-script to wait for X time then check if still paused. If paused kill.|
||[create_wait_kill_trans](../blob/master/killstream/create_wait_kill_trans.py)|Receive session_key from PlexPy when paused. Use session_id to create sub-script to wait for X time then check if transcoding still paused. If so, kill.|
||[kill_all_more_than](../blob/master/killstream/kill_all_more_than.py)|If user has 2 or more concurrent streams kill all streams|
||[kill_else_if_buffering](../blob/master/killstream/kill_else_if_buffering.py)|Kill concurrent transcode streams of other users if Admin user is experiencing buffering warnings from PlexPy.|
||[kill_more_than](../blob/master/killstream/kill_more_than.py)|If user has 2 or more concurrent streams and the IP of the 2nd stream differs from 1st kill 2nd. If 2nd stream IP is the same as 1st stream don't kill.|
||[kill_outsider_stream](../blob/master/killstream/kill_outsider_stream.py)|Kill stream if user is outside of local network.|
||[kill_plex_stream](../blob/master/killstream/kill_plex_stream.py)|Kill any Plex stream for whatever reason you want.|
||[kill_session_bitrate](../blob/master/killstream/kill_session_bitrate.py)|Kill stream if bitrate is greater than 4 Mbps|
||[kill_trans_exp_audio](../blob/master/killstream/kill_trans_exp_audio.py)|Kill Plex video transcoding streams only. All audio streams are left alone. Kill message based on platform.|
||[new_kill_trans_pause](../blob/master/killstream/new_kill_trans_pause.py)|Kill Plex paused video transcoding streams using PlexPy.|
|[Notify](../tree/master/notify "Notify")|||
||[find_unwatched_notify](../blob/master/notify/find_unwatched_notify.py)|Find what was added TFRAME ago and not watched and notify admin using PlexPy.|
||[notify_added_custom](../blob/master/notify/notify_added_custom.py)|Send an email with what was added to Plex in the past week using PlexPy. Email includes title (TV: Show Name: Episode Name; Movie: Movie Title), time added, image, and summary.|
||[notify_fav_tv_all_movie](../blob/master/notify/notify_fav_tv_all_movie.py)|Notify users of recently added episode to show that they have watched at least LIMIT times via email. Also notify users of new movies.|
||[notify_newip](../blob/master/notify/notify_newip.py)|If a new IP is found send notification via the Email Notification Agent. Email contains User's Avatar image, link to location, IP address, and User's Email address.|
||[notify_on_added](../blob/master/notify/notify_on_added.py)|Send an Email notification when a specific show is added to Plex. Add shows to list that you want notifications for.|
||[notify_user_favorites](../blob/master/notify/notify_user_favorites.py)|Notify users of recently added episode to show that they have watched at least LIMIT times via email.|
||[notify_user_newip](../blob/master/notify/notify_user_newip.py)|Notify user that their account has been accessed by a new IP. IP is cleared to make sure notification is sent again.|
||[twitter_notify](../blob/master/notify/twitter_notify.py)|Post to Twitter when TV/Movie is added to Plex. Include custom message and embed poster image. Option to tweet to TWITTER_USER if title is inside TITLE_FIND.|
