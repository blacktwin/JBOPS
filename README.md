# PlexPy-scripts

####Script Arguments:
-sn {show_name} -ena {episode_name} -ssn {season_num00} -enu {episode_num00} -srv {server_name} -med {media_type} -pos {poster_url} -tt {title} -sum {summary} -lbn {library_name} -ip {ip_address} -us {user} -uid {user_id} -pf {platform} -pl {player} -da {datestamp} -ti {timestamp}

####Enabling Scripts:

In the Notification Agents in the Settings menu. Click the Scripts gear. Your scripts location will be there. Can't remember if it's set automatically or not. If not, then set it where you'll keep your scripts. Scroll down to option you want to use and select the script from the drop down menu. Save. Click the Bell next to Scripts and enable Recently Added. Then click Notifications. Scroll down to Scripts. Enter in the Script Arguments found in the .py script. Save.

##notify_on_added.py:

This is based on the work from JonnyWong16/notify_on_show.py and mp998/PlexPy_email_notifiation.py. This is used to send an email notification when a specific show is added to Plex. Create a list of users with their email address and show preferences.

####Modify the User list, Email list, and Email settings.

User list: Show names need to match what Plex named it.
Email list: Make sure to expand the user_all list to include any new users added.

##notify_geomail.py:

This is based on the work from JonnyWong16/notify_geodata.py. Added user email information and changed email format to HTML. Email contain User's Avatar image, link to location, IP address, and User's Email address. Notification sent via the Email Notification Agent. Agent must be setup to work. 

##notify_newip.py:
Using notify_geomail.py as a base. If a new IP is found send notification via the Email Notification Agent. Agent must be setup to work. 
