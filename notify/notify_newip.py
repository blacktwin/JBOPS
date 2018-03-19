"""
Pulling together User IP information and Email.

Adding to Tautulli
Tautulli > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on playback start
Tautulli > Settings > Notification Agents > Scripts > Gear icon:
        Playback Start: notify_newip.py

Arguments passed from Tautulli
-sn {show_name} -ena {episode_name} -ssn {season_num00} -enu {episode_num00} -srv {server_name} -med {media_type}
-pos {poster_url} -tt {title} -sum {summary} -lbn {library_name} -ip {ip_address} -us {user} -uid {user_id}
-pf {platform} -pl {player} -da {datestamp} -ti {timestamp}


"""
import argparse
import requests
import sys

## EDIT THESE SETTINGS ##
TAUTULLI_APIKEY = ''  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL
NOTIFIER_ID = 12  # The notification notifier ID

# Replace LAN IP addresses that start with the LAN_SUBNET with a WAN IP address
# to retrieve geolocation data. Leave REPLACEMENT_WAN_IP blank for no replacement.
LAN_SUBNET = '192.168.0'
REPLACEMENT_WAN_IP = ''

# The notification subject and body
#   - Use "{p.argument}" for script arguments
#   - Use "{g.value}" for geolocation data
#   - Use "{u.value}" for user data
SUBJECT_TEXT = "New IP has been detected using Plex."
BODY_TEXT = """\
<html>
  <head></head>
  <body>
    <p>Hi!<br>
    <br><a href="mailto:{u.email}"><img src="{u.user_thumb}" alt="Poster unavailable" height="50" width="50"></a> 
    {p.user} has watched {p.media_type}:{p.title} from a new IP address: {p.ip_address}<br>
    <br>On {p.platform}[{p.player}] in 
    <a href="http://maps.google.com/?q={g.city},{g.country},{g.postal_code}">{g.city}, {g.country} {g.postal_code}</a>
     at {p.timestamp} on {p.datestamp}<br>
    <br><br>
    <br>User email is: {u.email}<br>
    </p>
  </body>
</html>
"""


class GeoData(object):
    def __init__(self, data=None):
        data = data or {}
        self.country = data.get('country', 'N/A')
        self.city = data.get('city', 'N/A')
        self.postal_code = data.get('postal_code', 'N/A')


class UserEmail(object):
    def __init__(self, data=None):
        data = data or {}
        self.email = data.get('email', 'N/A')
        self.user_id = data.get('user_id', 'N/A')
        self.user_thumb = data.get('user_thumb', 'N/A')


def get_user_ip_addresses(user_id='', ip_address=''):
    # Get the user IP list from Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_user_ips',
               'user_id': user_id,
               'search': ip_address}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        if response['response']['result'] == 'success':
            data = response['response']['data']
            if data.get('error'):
                raise Exception(data['error'])
            else:
                sys.stdout.write("Successfully retrieved UserIPs data.")
                if response['response']['data']['recordsFiltered'] == 0:
                    sys.stdout.write("IP has no history.")
                    return data
                else:
                    sys.stdout.write("IP has history, killing script.")
                    exit()
        else:
            raise Exception(response['response']['message'])
    except Exception as e:
        sys.stderr.write("Tautulli API 'get_user_ip_addresses' request failed: {0}.".format(e))
        return


def get_geoip_info(ip_address=''):
    # Get the geo IP lookup from Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_geoip_lookup',
               'ip_address': ip_address}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
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
        sys.stderr.write("Tautulli API 'get_geoip_lookup' request failed: {0}.".format(e))
        return GeoData()


def get_user_email(user_id=''):
    # Get the user email from Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_user',
               'user_id': user_id}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
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
        sys.stderr.write("Tautulli API 'get_user' request failed: {0}.".format(e))
        return UserEmail()


def send_notification(arguments=None, geodata=None, useremail=None):
    # Format notification text
    try:
        subject = SUBJECT_TEXT.format(p=arguments, g=geodata, u=useremail)
        body = BODY_TEXT.format(p=arguments, g=geodata, u=useremail)
    except LookupError as e:
        sys.stderr.write("Unable to substitute '{0}' in the notification subject or body".format(e))
        return None
    # Send the notification through Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'notify',
               'notifier_id': NOTIFIER_ID,
               'subject': subject,
               'body': body}

    try:
        r = requests.post(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        if response['response']['result'] == 'success':
            sys.stdout.write("Successfully sent Tautulli notification.")
        else:
            raise Exception(response['response']['message'])
    except Exception as e:
        sys.stderr.write("Tautulli API 'notify' request failed: {0}.".format(e))
        return None


if __name__ == '__main__':
    # Parse arguments from Tautulli
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
        get_user_ip_addresses(user_id=p.user_id, ip_address=p.ip_address)
        send_notification(arguments=p, geodata=g, useremail=u)

    else:
        sys.stdout.write("No IP address passed from Tautulli.")
