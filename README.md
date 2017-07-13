# JBOPS - Just a Bunch Of Plex Scripts

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=4J6RPWZ9J9YML) 

Scripts pulled from my gist profile. https://gist.github.com/blacktwin

### Script Arguments:
-sn {show_name} -ena {episode_name} -ssn {season_num00} -enu {episode_num00} -srv {server_name} -med {media_type} -pos {poster_url} -tt {title} -sum {summary} -lbn {library_name} -grk {grandparent_rating_key} -ip {ip_address} -us {user} -uid {user_id} -pf {platform} -pl {player} -da {datestamp} -ti {timestamp} -purl {plex_url}

#### Enabling Scripts:

In the Notification Agents in the Settings menu. Click the Scripts gear. Your scripts location will be there. Can't remember if it's set automatically or not. If not, then set it where you'll keep your scripts. Scroll down to option you want to use and select the script from the drop down menu. Save. Click the Bell next to Scripts and enable Recently Added. Then click Notifications. Scroll down to Scripts. Enter in the Script Arguments found in the .py script. Save.


## Scripts List

| Category | File | Description |
| :--- | :--- | :--- |
|[Fun](../tree/master/fun "Fun Fun")|[aired_today_playlist](https://github.com/blacktwin/JBOPS/blob/master/fun/aired_today_playlist.py) | Create a Plex Playlist with what was aired on this today's month-day, sort by oldest first. If Playlist from yesterday exists delete and create today's. If today's Playlist exists exit.|
||[plexapi_haiku](https://github.com/blacktwin/JBOPS/blob/master/fun/plexapi_haiku.py)| Create a hiaku from titles found in Plex.|
|[killstream](https://github.com/blacktwin/JBOPS/tree/master/killstream)| [create_wait_kill_all](https://github.com/blacktwin/JBOPS/blob/master/killstream/create_wait_kill_all.py)|Receive session_key from PlexPy when paused. Use session_id to create sub-script to wait for X time then check if still paused. If paused kill.|
||[create_wait_kill_trans](https://github.com/blacktwin/JBOPS/blob/master/killstream/create_wait_kill_trans.py)|Receive session_key from PlexPy when paused. Use session_id to create sub-script to wait for X time then check if transcoding still paused. If so, kill.|
||[kill_all_more_than](https://github.com/blacktwin/JBOPS/blob/master/killstream/kill_all_more_than.py)|If user has 2 or more concurrent streams kill all streams|
||[kill_else_if_buffering](https://github.com/blacktwin/JBOPS/blob/master/killstream/kill_else_if_buffering.py)|Kill concurrent transcode streams of other users if Admin user is experiencing buffering warnings from PlexPy.|
||[kill_more_than](https://github.com/blacktwin/JBOPS/blob/master/killstream/kill_more_than.py)|If user has 2 or more concurrent streams and the IP of the 2nd stream differs from 1st kill 2nd. If 2nd stream IP is the same as 1st stream don't kill.|
||[kill_outsider_stream](https://github.com/blacktwin/JBOPS/blob/master/killstream/kill_outsider_stream.py)|Kill stream if user is outside of local network.|
||[kill_plex_stream](https://github.com/blacktwin/JBOPS/blob/master/killstream/kill_plex_stream.py)|Kill any Plex stream for whatever reason you want.|
||[kill_session_bitrate](https://github.com/blacktwin/JBOPS/blob/master/killstream/kill_session_bitrate.py)|Kill stream if bitrate is greater than 4 Mbps|
||[kill_trans_exp_audio](https://github.com/blacktwin/JBOPS/blob/master/killstream/kill_trans_exp_audio.py)|Kill Plex video transcoding streams only. All audio streams are left alone. Kill message based on platform.|
||[new_kill_trans_pause](https://github.com/blacktwin/JBOPS/blob/master/killstream/new_kill_trans_pause.py)|Kill Plex paused video transcoding streams using PlexPy.|
