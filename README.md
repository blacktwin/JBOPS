
# JBOPS - Just a Bunch Of Plex Scripts

[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=4J6RPWZ9J9YML)  [![PM](https://img.shields.io/badge/Discord-Scripts-lightgrey.svg?colorB=7289da)](https://discord.gg/tQcWEUp) [![PM](https://img.shields.io/badge/Reddit-Message-lightgrey.svg)](https://www.reddit.com/user/Blacktwin/)  [![PM](https://img.shields.io/badge/Plex-Message-orange.svg)](https://forums.plex.tv/profile/discussions/Blacktwin) [![Issue](https://img.shields.io/badge/Submit-Issue-red.svg)](https://github.com/blacktwin/JBOPS/issues/new) 

Most of these scripts utilize a combination of [Tautulli](https://github.com/Tautulli/Tautulli), [python-plexapi](https://github.com/pkkid/python-plexapi), and [requests](http://docs.python-requests.org/en/master/user/install/#install).

For use of config.ini for common variables please use [plexapi.CONFIG](http://python-plexapi.readthedocs.io/en/latest/configuration.html)

Default location `~/.config/plexapi/config.ini`
```python
# To find path
import plexapi
print(plexapi.CONFIG_PATH)
```

## Notice:
Updated for Tautulli. Use plexpy-branch if you are still using PlexPy.

## Scripts List
[![Gist](https://img.shields.io/badge/gist-Blacktwin-green.svg)](https://gist.github.com/blacktwin)   

Scripts pulled from my gist profile. 

<details>
<summary><a href="https://github.com/blacktwin/JBOPS/tree/master/maps">Maps</a></summary>

<table>
  <tr>
    <th>Example</th>
    <th>File</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><a href="https://github.com/blacktwin/JBOPS/raw/master/maps/EU_map_example.PNG"><img src="https://img.shields.io/badge/Image-EU_map-blue.svg" alt=""</a>
    <a href="https://github.com/blacktwin/JBOPS/raw/master/maps/NA_map_example.PNG"><img src="https://img.shields.io/badge/Image-NA_map-blue.svg" alt=""</a>
    <a href="https://github.com/blacktwin/JBOPS/raw/master/maps/World_map_example.PNG"><img src="https://img.shields.io/badge/Image-World_map-blue.svg" alt=""</a>
    <a href="https://github.com/blacktwin/JBOPS/blob/master/maps/geojson_example.geojson"><img src="https://img.shields.io/badge/Image-geojson-blue.svg" alt=""</a></td>
    <td><a href="../master/maps/ips_to_maps.py"ips_to_maps>Maps</a></td>
    <td>Using Tautulli data, draw a map connecting Server to Clients based on IP addresses.</td>
  </tr>
</table>
</details>

<details>
<summary><a href="https://github.com/blacktwin/JBOPS/tree/master/fun">Fun</a></summary>

<table>
  <tr>
    <th>Gist</th>
    <th>File</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/397f07724abebd1223ba6ea644ea1669"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/fun/aired_today_playlist.py">aired_today_playlist</a></td>
    <td>Create a Plex Playlist with what was aired on this today's month-day, sort by oldest first. If Playlist from yesterday exists delete and create today's. If today's Playlist exists exit.</td>
  </tr>
    <tr>
    <td><a href="https://gist.github.com/blacktwin/4ccb79c7d01a95176b8e88bf4890cd2b"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/fun/plexapi_haiku.py">plexapi_haiku</a></td>
    <td>Create a hiaku from titles found in Plex.</td>
  </tr>
</table>
</details>


<details>
<summary><a href="https://github.com/blacktwin/JBOPS/tree/master/killstream">Kill stream</a></summary>

<table>
Killing streams is a Plex Pass only feature. So these scripts will only work for Plex Pass users.
  <tr>
    <th>Gist</th>
    <th>File</th>
    <th>Description</th>
  </tr>
  <tr>
    <td></td>
    <td><a href="../master/killstream/wait_kill_pause_notify_main.py">wait_kill_pause_notify_main</a></td>
    <td>
	Receive session_key from Tautulli when paused. Use sub-script <a href="../master/killstream/wait_kill_pause_notify_sub.py">wait_kill_pause_notify_sub</a>
	to wait for X time then check if still paused. If so, kill. Toggle whether you'd like to be notified through a Tautulli notification agent.
	</td>
  </tr>
  <tr>
    <td></td>
    <td><a href="../master/killstream/watch_limit.py">watch_limit</a></td>
    <td>Kill streams if user has watched too much Plex Today.</td>
  </tr>
  <tr>
  <tr>
    <td></td>
    <td><a href="../master/killstream/play_limit.py">play_limit</a></td>
    <td>Kill streams if user has played too much Plex Today.</td>
  </tr>
  <tr>
    <td></td>
    <td><a href="../master/killstream/kill_time.py">kill_time</a></td>
    <td>Limit number of plays of TV Show episodes during time of day. Idea is to reduce continuous plays while sleeping.</td>
  </tr>
   <tr>
    <td></td>
    <td><a href="../master/killstream/kill_trans_pause_notify.py">kill_trans_pause_notify</a></td>
    <td>Kill Plex paused video transcoding streams and receive notification.</td>
  </tr>
  <tr>
    <td></td>
    <td><a href="../master/killstream/ip_whitelist.py">ip_whitelist</a></td>
    <td>Receive session_key and IP from Tautulli when playback starts. Use IP to check against whitelist. If not in whitelist use session_key to determine stream and kill.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/88fce565c8ecf56839641f22f4c5c422"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/killstream/kill_all_more_than.py">kill_all_more_than</a></td>
    <td>If user has 2 or more concurrent streams kill all streams</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/d47d3ada86d02a494f9dc33e50dd15b5"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/killstream/kill_else_if_buffering.py">kill_else_if_buffering</a></td>
    <td>Kill concurrent transcode streams of other users if Admin user is experiencing buffering warnings from Tautulli.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/6d08b94ca3e80d3ed0bb3c7172fae21d"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/killstream/kill_more_than.py">kill_more_than</a></td>
    <td>If user has 2 or more concurrent streams and the IP of the 2nd stream differs from 1st kill 2nd. If 2nd stream IP is the same as 1st stream don't kill.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/eee23eeb95f1285fbb495c5a8592b242"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/killstream/kill_outsider_stream.py">kill_outsider_stream</a></td>
    <td>Kill stream if user is outside of local network.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/8b174165cfc5e5e80c6698a1494fc9ee"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/killstream/kill_plex_streams.py">kill_plex_streams</a></td>
    <td>Kill all Plex streams for whatever reason you want.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/77f6f1be32621ed71655ca27406ef772"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/killstream/kill_session_bitrate.py">kill_session_bitrate</a></td>
    <td>Kill stream if bitrate is greater than 4 Mbps</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/0e6207346acfaaca602eb7dce80226a0"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/killstream/kill_trans_exp_audio.py">kill_trans_exp_audio</a></td>
    <td>Kill Plex video transcoding streams only. All audio streams are left alone. Kill message based on platform.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/14d400a0f442da465389164fa046647a"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/killstream/kill_trans_pause.py">kill_trans_pause</a></td>
    <td>Kill Plex paused video transcoding streams using Tautulli.</td>
  </tr>
</table>
</details>


<details>
<summary><a href="https://github.com/blacktwin/JBOPS/tree/master/notify">Notify</a></summary>

<table>
  <tr>
    <th>Gist</th>
    <th>File</th>
    <th>Description</th>
  </tr>
    <tr>
    <td></td>
    <td><a href="../master/notify/notify_delay.py">notify_delay</a></td>
    <td>Delay Notification Agent message for concurrent streams.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/e6d589a9af9bdf168717951083861e93"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/notify/find_unwatched_notify.py">find_unwatched_notify</a></td>
    <td>Find what was added TFRAME ago and not watched and notify admin using Tautulli.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/1094dcf38249f36c8d374e0cba7a86cd"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/notify/notify_added_custom.py">notify_added_custom</a></td>
    <td>Send an email with what was added to Plex in the past week using Tautulli. Email includes title (TV: Show Name: Episode Name; Movie: Movie Title), time added, image, and summary.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/099c07d8099c18a378bba6415d9253ba"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/notify/notify_fav_tv_all_movie.py">notify_fav_tv_all_movie</a></td>
    <td>Notify users of recently added episode to show that they have watched at least LIMIT times via email. Also notify users of new movies.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/a2d4b2f2c3b616f1d6da0752fecb2ae7"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/notify/notify_newip.py">notify_newip</a></td>
    <td>If a new IP is found send notification via the Email Notification Agent. Email contains User's Avatar image, link to location, IP address, and User's Email address.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/a327055da54d7feb3eef10e64a8b661a"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/notify/notify_on_added.py">notify_on_added</a></td>
    <td>Send an Email notification when a specific show is added to Plex. Add shows to list that you want notifications for.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/18960ff01c03b67a05594daa6f53660c"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/notify/notify_user_favorites.py">notify_user_favorites</a></td>
    <td>Notify users of recently added episode to show that they have watched at least LIMIT times via email.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/066c66328a795ebd6079a575e14f0b8b"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/notify/notify_user_newip.py">notify_user_newip</a></td>
    <td>Notify user that their account has been accessed by a new IP. IP is cleared to make sure notification is sent again.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/261c416dbed08291e6d12f6987d9bafa"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/notify/twitter_notify.py">twitter_notify</a></td>
    <td>Post to Twitter when TV/Movie is added to Plex. Include custom message and embed poster image. Option to tweet to TWITTER_USER if title is inside TITLE_FIND.</td>
  </tr>
</table>
</details>


<details>
<summary><a href="https://github.com/blacktwin/JBOPS/tree/master/utility">Utility</a></summary>

<table>
  <tr>
    <th>Gist</th>
    <th>File</th>
    <th>Description</th>
  </tr>
  <tr>
    <td></td>
    <td><a href="../master/utility/plex_api_parental_control.py">plex_api_parental_control</a></td>
    <td>Set as cron or task for times of allowing and not allowing user access to server. Unsharing will kill any current stream from user before unsharing.</td>
  </tr>
   <tr>
    <td></td>
    <td><a href="../master/utility/plex_api_share.py">plex_api_share</a></td>
    <td>Share or unshare libraries</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/f4149c296f2d1ffd1cbd863c37bb3a3c"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/utility/bypass_auth_name.py">bypass_auth_name</a></td>
    <td>Use Tautulli to pull last IP address from user and add to List of IP addresses and networks that are allowed without auth in Plex.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/0332f2dc9534bdf412ff3f664e9513c0"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/utility/delete_watched_TV.py">delete_watched_TV</a></td>
    <td>From a list of TV shows, check if users in a list has watched shows episodes. If all users in list have watched an episode of listed show, then delete episode.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/76b0abf88181618af4598092dd6b0dbb"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/utility/find_plex_meta.py">find_plex_meta</a></td>
    <td>Find location of Plex metadata.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/603d5da5b70b366e98d0d82d1aa1a470"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/utility/find_unwatched.py">find_unwatched</a></td>
    <td>Find what was added TFRAME ago and not watched using Tautulli.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/f435aa0ccd498b0840d2407d599bf31d"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/utility/grab_gdrive_media.py">grab_gdrive_media</a></td>
    <td>Grab media (videos, pictures) from Google Drive. All videos and pictures were automatically synced from Google Photos to Google Drive. Puts media into MEDIA_TYPE/YEAR/MONTH-DAY/FILE.ext directory structure.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/85a63ffd70c6ccb7c1faa70a8f33fc2e"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/utility/plex_api_poster_pull.py">plex_api_poster_pull</a></td>
    <td>Pull Movie and TV Show poster images from Plex.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/17b58156f69cc52026b71fe4d5afea05"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/utility/plex_imgur_dl.py">plex_imgur_dl</a></td>
    <td>Pull poster images from Imgur and places them inside Shows root folder.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/f10e0a1e85af00e878963b4570a99054"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/utility/plex_theme_songs.py">plex_theme_songs</a></td>
    <td>Download theme songs from Plex TV Shows.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/45c420cbba4e18aadc8cc5090a67b9d1"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/utility/plexapi_delete_playlists.py">plexapi_delete_playlists</a></td>
    <td>Delete all playlists from Plex using PlexAPI.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/df58032de3e6f4d29f7ea562aeaebbab"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/utility/plexapi_search_file.py">plexapi_search_file</a></td>
    <td>Find full path for Plex items.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/3752a76fa0b3fc6d19e842af7b812184"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/utility/refresh_next_episode.py">refresh_next_episode</a></td>
    <td>Refresh the next episode of show once current episode is watched.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/370ca42ee20a33fb00c8253fa9bd0de7"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/utility/remove_watched_movies.py">remove_watched_movies</a></td>
    <td>Find Movies that have been watched by a list of users. If all users have watched movie then delete.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/2f619e62d99edcec27f680998379664c"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/utility/stream_limiter_ban_email.py">stream_limiter_ban_email</a></td>
    <td>This is indented to restrict a user to the LIMIT amount of concurrent streams. User will be warned, punished, and banned completely if violations continue.</td>
  </tr>
</table>
</details>

<details>
<summary><a href="https://github.com/blacktwin/JBOPS/tree/master/reporting">Reporting</a></summary>

<table>
  <tr>
    <th>Gist</th>
    <th>File</th>
    <th>Description</th>
  </tr>
  <tr>
    <td></td>
    <td><a href="../master/reporting/weekly_stats_reporting.py">weekly_stats_reporting</a></td>
    <td>Pull library and user statistics of last week.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/21823b3394f5b077d42495b21570b593"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/reporting/added_to_plex.py">added_to_plex</a></td>
    <td>Find when media was added between STARTFRAME and ENDFRAME to Plex through Tautulli.</td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/f070dff29ddbeb87973be9c0a94a1df7"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/reporting/check_play.py">check_play</a></td>
    <td>Check if user has play a file more than 3 times but has not finished watching. Hoping to catch play failures.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/1a8933252ad1a9bc2c97395a020c144a"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/reporting/check_plex_log.py">check_plex_log</a></td>
    <td>Checking plex logs for debug code WARN and 'Failed to obtain a streaming resource for transcode of key /library/metadata/"titleID"'.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/561c3a404754eb7b9e543867619d3251"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/reporting/drive_check.py">drive_check</a></td>
    <td>Check if drive exists. If not then notify via Tautulli notifier agent.    </td>
  </tr>
  <tr>
    <td><a href="https://gist.github.com/blacktwin/bd905d39ab71c5d7c628e27fddd1086e"><img src="https://img.shields.io/badge/gist-original-green.svg"></a></td>
    <td><a href="../master/reporting/userplays_weekly_reporting.py">userplays_weekly_reporting</a></td>
    <td>Use Tautulli to count how many plays per user occurred this week and send email via Tautulli.</td>
  </tr>

</table>
</details>

----

<details>
<summary>Setting Up Tautulli for Custom Scripts</summary>

#### Enabling Scripts in Tautulli:

Taultulli > Settings > Notification Agents > Add a Notification Agent > Script

#### Configuration

Taultulli > Settings > Notification Agents > New Script > Configuration:
- [ ] Set scripts location to location of your script
- [ ] Scroll down to option you want to use and select the script from the drop down menu
- [ ] Set desired Script Timeout value
- [ ] Optional - Add a description of the script for easy reference
- [ ] Save
      
#### Triggers
Taultulli > Settings > Notification Agents > New Script > Triggers:

- [ ] Check desired trigger
- [ ] Save

#### Conditions
Taultulli > Settings > Notification Agents > New Script > Conditions:

- [ ] Set desired conditions
- [ ] Save

For more information on Tautulli conditions see [here](https://github.com/Tautulli/Tautulli-Wiki/wiki/Custom-Notification-Conditions)

#### Script Arguments
Taultulli > Settings > Notification Agents > New Script > Script Arguments:

- [ ] Select desired trigger
- [ ] Input desired notification parameters (List of parameters will likely be found inside script)
- [ ] Save
- [ ] Close


</details>

---
<details>
<summary>Common variables</summary>

<details>
<summary>Plex</summary>

- [ ]  PLEX_URL - Local/Remote IP to connect to Plex ('http://localhost:32400', 'https://x.x.x.x:32412', etc.)
- [ ]  PLEX_TOKEN - [Plex](https://support.plex.tv/hc/en-us/articles/204059436-Finding-an-authentication-token-X-Plex-Token) or Tautulli Settings > Plex.tv Account > PMS Token
</details>

<details>
<summary>Tautulli</summary>

- [ ]  TAUTULLI_URL - Local/Remote IP to connect to Tautulli ('http://localhost:8181',  'https://x.x.x.x:8182', etc.)
- [ ]  TAUTULLI_APIKEY - Tautulli Settings > Access Control > Enable API - API Key
</details>

</details>
