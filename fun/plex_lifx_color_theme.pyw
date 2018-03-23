#
# Author: Bailey Belvis (https://github.com/philosowaffle)
#
# Will dim your lifx lights and set them to a color theme matching the currently
# playing media.
#
# - Enable `Upload Posters to Imgur for Notifications` - required for lights to match the posters color scheme
# - Triggers - PlexLifx supports the following triggers, enable the ones you are interested in.
#	    - Notify on Playback Start
#	    - Notify on Playback Stop
#	    - Notify on Playback Resume
# 	  - Notify on Playback Pause
#
# - Copy paste the following line to each of the Triggers you enabled (found on the Arguments tab):
# 	-a {action} -mt {media_type} -mi {machine_id} -rk {rating_key} -pu {poster_url}
#
import os
import sys
import logging
import hashlib
import shutil
import numpy
import argparse
import urllib

from random import shuffle
from pifx import PIFX
from colorthief import ColorThief

######################################
# Configuration - EDIT THESE SETTINGS
######################################

LogFile = "plex_lifx.log"

# List of Player Id's that should trigger this script.  In order to identify your
# players UUID, enter a dummy id, enable the script, and start playing some media
# on the target device.  In the Tautulli logs, search for `plex_lifx`, the UUID should
# appear there.
PlayerUUIDs = ""

# LIFX API Key
APIKey = ""

# Bulb Brightness when media is playing
Brightness = .25

# Transition duration
Duration = 3.0

# Number of colors to be used across your lights
NumColors = 5

# How closely the colors should match the media thumbnail, 10 is the highest
ColorQuality = 10

# Default theme to restore lights to on media pause/stop
DefaultPauseTheme = "Basic"

# Default theme to set lights to when media poster fails
DefaultPlayTheme = "Blue"

# Lights that should be controlled by this script, the order the lights are specified in will effect the order in which colors are applied.
# You can play around with different light orders until you find one that spreads the colors how you like.  You can also configure more
# or fewer colors above (see 'NumColors') in order to increase or decrease the amount of color diversity across lights.
Lights = "Corner Lamp,Kitchen Lamp,Standing Lamp 1,Standing Lamp 3,Standing Lamp 2,Bedroom Lamp,Tall Corner Lamp,Titan Lamp"

##############################
# Logging Setup
##############################

logger = logging.getLogger('plex_lifx')
logger.setLevel(logging.DEBUG)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s: %(message)s')

# File Handler
file_handler = logging.FileHandler(LogFile)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.debug("Starting Plex+Lifx Script :)")

##############################
# Plex Setup
##############################

filtered_players = [] if PlayerUUIDs == "none" else PlayerUUIDs.split(',')

logger.debug("Filtered Players: " + filtered_players.__str__())

events = [
	'play',
	'pause',
	'resume',
	'stop'
]

##############################
# LIFX Setup
##############################

brightness = Brightness if Brightness else .35
duration = Duration if Duration else 2.0
num_colors = NumColors if NumColors else 4
color_quality = ColorQuality if ColorQuality else 1

if not APIKey:
	logger.error("Missing LIFX API Key")
	exit(1)
else:
	lifx_api_key = APIKey
	logger.debug("LIFX API Key: " + lifx_api_key)

pifx = PIFX(lifx_api_key)

lights = []
if Lights:
	lights_use_name = True
	lights = Lights.split(',')

	tmp = []
	for light in lights:
		tmp.append(light.strip())
	lights = tmp
else:
	lights_detail = pifx.list_lights()
	for light in lights_detail:
		lights.append(light['id'])
	shuffle(lights)

scenes_details = pifx.list_scenes()
scenes = dict()
for scene in scenes_details:
	scenes[scene['name']] = scene['uuid']

logger.debug(scenes)
logger.debug(lights)

default_pause_theme = DefaultPauseTheme
default_play_theme = DefaultPlayTheme

default_pause_uuid = scenes[default_pause_theme]
default_play_uuid = scenes[default_play_theme]

number_of_lights = len(lights)
if number_of_lights < num_colors:
	num_colors = number_of_lights

light_groups = numpy.array_split(numpy.array(lights), num_colors)

logger.debug("Number of Lights: " + color_quality.__str__())
logger.debug("Number of Colors: " + num_colors.__str__())
logger.debug("Color Quality: " + color_quality.__str__())

##############################
# Arg Parser
##############################
p = argparse.ArgumentParser()
p.add_argument('-a', '--action', action='store', default='',
                    help='The action that triggered the script.')
p.add_argument('-mt', '--media_type', action='store', default='',
                    help='The media type of the media being played.')
p.add_argument('-mi', '--machine_id', action='store', default='',
                    help='The machine id of where the media is playing.')
p.add_argument('-rk', '--rating_key', action='store', default='',
                    help='The unique identifier for the media.')
p.add_argument('-pu', '--poster_url', action='store', default='',
                    help='The poster url for the media playing.')

parser = p.parse_args()

##############################
# Script Begin
##############################

event = parser.action
media_type = parser.media_type
player_uuid = parser.machine_id
media_guid = parser.rating_key
poster_url = parser.poster_url

logger.debug("Event: " + event)
logger.debug("Media Type: " + media_type)
logger.debug("Player UUI: " + player_uuid)
logger.debug("Media Guid: " + media_guid)
logger.debug("Poster Url: " + poster_url)

# Only perform action for event play/pause/resume/stop for TV and Movies
if not event in events:
	logger.debug("Invalid action: " + event)
	exit()

if (media_type != "movie") and (media_type != "episode"):
	logger.debug("Media type was not movie or episode, ignoring.")
	exit()

# If we configured only specific players to be able to play with the lights
if filtered_players:
	try:
		if player_uuid  not in filtered_players:
			logger.info(player_uuid + " player is not able to play with the lights")
			exit()
	except Exception as e:
		logger.error("Failed to check uuid - " + e.__str__())

# Setup Thumbnail directory paths
upload_folder = os.getcwd() + '\\tmp'
thumb_folder = os.path.join(upload_folder, media_guid)
thumb_path = os.path.join(thumb_folder, "thumb.jpg")

if event == 'stop':
	if os.path.exists(thumb_folder):
		logger.debug("Removing Directory: " + thumb_folder)
		shutil.rmtree(thumb_folder)

	pifx.activate_scene(default_pause_uuid)
	exit()

if event == 'pause':
	pifx.activate_scene(default_pause_uuid)
	exit()

if event == 'play' or event == "resume":

	# If the file already exists then we don't need to re-upload the image
	if not os.path.exists(thumb_folder):
		try:
			logger.debug("Making Directory: " + thumb_folder)
			os.makedirs(thumb_folder)
			urllib.urlretrieve(poster_url, thumb_path)
		except Exception as e:
			logger.error(e)
			logger.info("No file found in request")
			pifx.activate_scene(default_play_uuid)
			exit()			

    # Determine Color Palette for Lights
	color_thief = ColorThief(thumb_path)
	palette = color_thief.get_palette(color_count=num_colors, quality=color_quality)
	logger.debug("Color Palette: " + palette.__str__())

    # Set Color Palette
	pifx.set_state(selector='all', power="off")
	for index in range(len(light_groups)):
		try:
			color = palette[index]
			light_group = light_groups[index]

			logger.debug(light_group)
			logger.debug(color)

			color_rgb = ', '.join(str(c) for c in color)
			color_rgb = "rgb:" + color_rgb
			color_rgb = color_rgb.replace(" ", "")

			for light_id in light_group:
				if lights_use_name:
					selector = "label:" + light_id
				else:
					selector = light_id

				logger.debug("Setting light: " + selector + " to color: " + color_rgb)
				pifx.set_state(selector=selector, power="on", color=color_rgb, brightness=brightness, duration=duration)
			
		except Exception as e:
			logger.error(e)

exit()
