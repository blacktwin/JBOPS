#   1. Install the requests module for python.
#       pip install requests
#   2. Add script arguments in PlexPy. The following script arguments are available by default. More can be added below.
#      -ip {ip_address} -us {user} -med {media_type} -tt {title} -pf {platform} -pl {player} -da {datestamp} -ti {timestamp}

import argparse
import requests
import sys


## EDIT THESE SETTINGS ##

PLEXPY_APIKEY = '56953cf8a660652acb20ce40c90f2b19'  # Your PlexPy API key
PLEXPY_URL = 'http://localhost:8182/'  # Your PlexPy URL
AGENT_ID = 10  # The notification agent ID for PlexPy
# 10 Email
# 15 Scripts
# 17 Browser

# Replace LAN IP addresses that start with the LAN_SUBNET with a WAN IP address
# to retrieve geolocation data. Leave REPLACEMENT_WAN_IP blank for no replacement.
LAN_SUBNET = ('10.201', '127.0.0')
REPLACEMENT_WAN_IP = '199.15.252.230'

# The notification subject and body
#   - Use "{p.argument}" for script arguments
#   - Use "{g.value}" for geolocation data
#   - Use "{u.value}" for user data
SUBJECT_TEXT = "PlexPy Notification"
BODY_TEXT = """\
<html>
  <head></head>
  <body>
	<p>Hi!<br>
	<br><a href="mailto:{u.email}"><img src="{u.user_thumb}" alt="Poster unavailable" height="50" width="50"></a> {p.user} has watched {p.media_type}:{p.title}<br>
	<br>On {p.platform}[{p.player}] in <a href="http://maps.google.com/?q={g.latitude},{g.longitude}">{g.city}, {g.country}</a>.<br>
	<br>At {p.timestamp} on {p.datestamp}.<br>
	<br>IP address: {p.ip_address}<br>
	<br>User email is: {u.email}<br>
	<br>TEst area Data:{uip.data} <br>
	</p>
  </body>
</html>
"""

## CODE BELOW ##

##Geo Space##
class GeoData(object):
	def __init__(self, data=None):
		data = data or {}
		self.continent = data.get('continent', 'N/A')
		self.country = data.get('country', 'N/A')
		self.region = data.get('region', 'N/A')
		self.city = data.get('city', 'N/A')
		self.postal_code = data.get('postal_code', 'N/A')
		self.timezone = data.get('timezone', 'N/A')
		self.latitude = data.get('latitude', 'N/A')
		self.longitude = data.get('longitude', 'N/A')
		self.accuracy = data.get('accuracy', 'N/A')

##USER Space##
class UserEmail(object):
	def __init__(self, data=None):
		data = data or {}
		self.email = data.get('email', 'N/A')
		self.user_id = data.get('user_id', 'N/A')
		self.user_thumb = data.get('user_thumb', 'N/A')

##API Space##
def get_geoip_info(ip_address=''):
	# Get the geo IP lookup from PlexPy
	payload = {'apikey': PLEXPY_APIKEY,
			   'cmd': 'get_geoip_lookup',
			   'ip_address': ip_address}

	try:
		r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
		response = r.json()

		if response['response']['result'] == 'success':
			data = response['response']['data']
			if data.get('error'):
				raise Exception(data['error'])
			else:
				sys.stdout.write("Successfully retrieved geolocation data.")
				return GeoData(data=data)
		else:
			raise Exception(response['response']['message'])
	except Exception as e:
		sys.stderr.write("PlexPy API 'get_geoip_lookup' request failed: {0}.".format(e))
		return GeoData()


def get_user_email(user_id=''):
	# Get the user email from PlexPy
	payload = {'apikey': PLEXPY_APIKEY,
			   'cmd': 'get_user',
			   'user_id': user_id}

	try:
		r = requests.get(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
		response = r.json()

		if response['response']['result'] == 'success':
			data = response['response']['data']
			if data.get('error'):
				raise Exception(data['error'])
			else:
				sys.stdout.write("Successfully retrieved user email data.")
				return UserEmail(data=data)
		else:
			raise Exception(response['response']['message'])
	except Exception as e:
		sys.stderr.write("PlexPy API 'get_user' request failed: {0}.".format(e))
		return UserEmail()

def send_notification(arguments=None, geodata=None, useremail=None, user_address=None):
	# Format notification text
	try:
		subject = SUBJECT_TEXT.format(p=arguments, g=geodata, u=useremail)
		body = BODY_TEXT.format(p=arguments, g=geodata, u=useremail)
	except LookupError as e:
		sys.stderr.write("Unable to substitute '{0}' in the notification subject or body".format(e))
		return None
	# Send the notification through PlexPy
	payload = {'apikey': PLEXPY_APIKEY,
			   'cmd': 'notify',
			   'agent_id': AGENT_ID,
			   'subject': subject,
			   'body': body}

	try:
		r = requests.post(PLEXPY_URL.rstrip('/') + '/api/v2', params=payload)
		response = r.json()
		
		if response['response']['result'] == 'success':
			sys.stdout.write("Successfully sent PlexPy notification.")
		else:
			raise Exception(response['response']['message'])
	except Exception as e:
		sys.stderr.write("PlexPy API 'notify' request failed: {0}.".format(e))
		return None

if __name__ == '__main__':
	# Parse arguments from PlexPy
	parser = argparse.ArgumentParser()

	parser.add_argument('-ip', '--ip_address', action='store', default='',
						help='The IP address of the stream')
	parser.add_argument('-us', '--user', action='store', default='',
						help='Username of the person watching the stream')
	parser.add_argument('-uid', '--user_id', action='store', default='',
						help='User_ID of the person watching the stream')						
	parser.add_argument('-med', '--media_type', action='store', default='',
						help='The media type of the stream')
	parser.add_argument('-tt', '--title', action='store', default='',
						help='The title of the media')
	parser.add_argument('-pf', '--platform', action='store', default='',
						help='The platform of the stream')
	parser.add_argument('-pl', '--player', action='store', default='',
						help='The player of the stream')
	parser.add_argument('-da', '--datestamp', action='store', default='',
						help='The date of the stream')
	parser.add_argument('-ti', '--timestamp', action='store', default='',
						help='The time of the stream')
	parser.add_argument('-sn', '--show_name', action='store', default='',
						help='The name of the TV show')
	parser.add_argument('-ena', '--episode_name', action='store', default='',
						help='The name of the episode')
	parser.add_argument('-ssn', '--season_num', action='store', default='',
						help='The season number of the TV show')
	parser.add_argument('-enu', '--episode_num', action='store', default='',
						help='The episode number of the TV show')
	parser.add_argument('-srv', '--plex_server', action='store', default='',
						help='The name of the Plex server')
	parser.add_argument('-pos', '--poster', action='store', default='',
						help='The poster url')
	parser.add_argument('-sum', '--summary', action='store', default='',
						help='The summary of the TV show')
	parser.add_argument('-lbn', '--library_name', action='store', default='',
						help='The name of the TV show')
						
	p = parser.parse_args()

	# Check to make sure there is an IP address before proceeding
	if p.ip_address:
		if p.ip_address.startswith(LAN_SUBNET) and REPLACEMENT_WAN_IP:
			ip_address = REPLACEMENT_WAN_IP
		else:
			ip_address = p.ip_address
			
		g = get_geoip_info(ip_address=ip_address)
		u = get_user_email(user_id=p.user_id)
		send_notification(arguments=p, geodata=g, useremail=u)
		
	else:
		sys.stdout.write("No IP address passed from PlexPy.")
