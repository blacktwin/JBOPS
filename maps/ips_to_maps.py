"""
Use Tautulli draw a map connecting Server to Clients based on IP addresses.

optional arguments:
  -h, --help            show this help message and exit
  -l , --location       Map location. choices: (NA, EU, World, Geo)
                        (default: NA)
  -c [], --count []     How many IPs to attempt to check.
                        (default: 2)
  -u  [ ...], --users  [ ...]
                        Space separated list of case sensitive names to process. Allowed names are:
                        {List of Users}
                        (default: all)
  -i  [ ...], --ignore  [ ...]
                        Space separated list of case sensitive names to process. Allowed names are:
                        {List of Users}
                        (default: None)
  -f  [ ...], --filename  [ ...]
                        Filename of map. None will not save. (default: Map_YYYYMMDD-HHMMSS)
  -j [], --json []      Filename of json file to use.
                        (choices: {List of .json files in current dir})
  --headless            Run headless.


"""

import requests
import sys
import json
import os
from collections import OrderedDict
import argparse
import numpy as np
import time
import webbrowser
import re

## EDIT THESE SETTINGS ##
TAUTULLI_APIKEY = ''  # Your Tautulli API key
TAUTULLI_URL = 'http://localhost:8181/'  # Your Tautulli URL

# Replace LAN IP addresses that start with the LAN_SUBNET with a WAN IP address
# to retrieve geolocation data. Leave REPLACEMENT_WAN_IP blank for no replacement.
LAN_SUBNET = ('10.10', '127.0.0')
REPLACEMENT_WAN_IP = ''

# Enter Friendly name for Server ie 'John Smith'
SERVER_FRIENDLY = 'Server'

# Server location information. Find this information on your own.
# If server plot is out of scope add print(geo_lst) after ut.user_id loop ~line 151 to find the error
SERVER_LON = ''
SERVER_LAT = ''
SERVER_CITY = ''
SERVER_STATE = ''
SERVER_PLATFORM = 'Server'

DEFAULT_COLOR = '#A96A1C'  # Plex Orange?

PLATFORM_COLORS = {'Android': '#a4c639',  # Green
                   'Roku': '#800080',  # Purple
                   'Chromecast': '#ffff00',  # Yellow
                   'Xbox One': '#ffffff',  # White
                   'Chrome': '#ff0000',  # Red
                   'Playstation 4': '#0000ff',  # Blue
                   'iOS': '#8b4513',  # Poop brown
                   'Samsung': '#0c4da2',  # Blue
                   'Windows': DEFAULT_COLOR,
                   'Xbox 360 App': DEFAULT_COLOR}

# title of map
title_string = "Location of Plex users based on ISP data"


def clean_up_text(title):
    cleaned = re.sub('\W+', ' ', title)
    return cleaned


class GeoData(object):
    def __init__(self, data=None):
        data = data or {}
        self.continent = data.get('continent', 'N/A')
        self.country = data.get('country', 'N/A')
        self.region = clean_up_text(data.get('region', 'N/A'))
        self.city = clean_up_text(data.get('city', 'N/A'))
        self.postal_code = data.get('postal_code', 'N/A')
        self.timezone = data.get('timezone', 'N/A')
        self.latitude = data.get('latitude', 'N/A')
        self.longitude = data.get('longitude', 'N/A')
        self.accuracy = data.get('accuracy', 'N/A')


class UserIPs(object):
    def __init__(self, data=None):
        d = data or {}
        self.ip_address = d['ip_address']
        self.friendly_name = clean_up_text(d['friendly_name'])
        self.play_count = d['play_count']
        self.platform = d['platform']


def get_users_tables(users='', length=''):
    # Get the users list from Tautulli

    if length:
        payload = {'apikey': TAUTULLI_APIKEY,
                   'cmd': 'get_users_table',
                   'length': length}
    else:
        payload = {'apikey': TAUTULLI_APIKEY,
                   'cmd': 'get_users_table'}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']['data']
        if not length and not users:
            # Return total user count
            return response['response']['data']['recordsTotal']
        else:
            if users == 'all':
                return [d['user_id'] for d in res_data]
            elif users == 'friendly_name':
                return [d['friendly_name'] for d in res_data]
            else:
                return [d['user_id'] for user in users for d in res_data if user == d['friendly_name']]

    except Exception as e:
        sys.stderr.write("Tautulli API 'get_users_tables' request failed: {0}.".format(e))


def get_users_ips(user_id, length):
    # Get the user IP list from Tautulli
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_user_ips',
               'user_id': user_id}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()
        res_data = response['response']['data']['data']
        return [UserIPs(data=d) for d in res_data]
    except Exception as e:
        sys.stderr.write("Tautulli API 'get_users_ips' request failed: {0}.".format(e))


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
        pass


def add_to_dictlist(d, key, val):
    if key not in d:
        d[key] = [val]
    else:
        d[key].append(val)
    for x in d[key]:
        if (val['region'], val['city']) == (x['region'], x['city']):
            x['location_count'] += 1


def get_geo_dict(length, users):
    geo_dict = {SERVER_FRIENDLY: [{'lon': SERVER_LON, 'lat': SERVER_LAT, 'city': SERVER_CITY, 'region': SERVER_STATE,
                                   'ip': REPLACEMENT_WAN_IP, 'play_count': 0, 'platform': SERVER_PLATFORM,
                                   'location_count': 0}]}

    for i in get_users_tables(users):
        user_ip = get_users_ips(user_id=i, length=length)
        city_cnt = 0
        for a in user_ip:
            try:
                ip = a.ip_address
                if ip.startswith(LAN_SUBNET) and REPLACEMENT_WAN_IP:
                    ip = REPLACEMENT_WAN_IP

                g = get_geoip_info(ip_address=ip)

                add_to_dictlist(geo_dict, a.friendly_name, {'lon': str(g.longitude), 'lat': str(g.latitude),
                                                            'city': str(g.city), 'region': str(g.region),
                                                            'ip': ip, 'play_count': a.play_count,
                                                            'platform': a.platform, 'location_count': city_cnt})
            except AttributeError:
                print('User: {} IP: {} caused error in geo_dict.'.format(a.friendly_name, a.ip_address))
                pass
            except Exception as e:
                print('Error here: {}'.format(e))
                pass
    return geo_dict


def get_geojson_dict(user_locations):
    locs = []
    for username, locations in user_locations.iteritems():
        for location in locations:
            try:
                locs.append({
                    "type": "Feature",
                    "properties": {
                        "User": username,
                        "City": location['city'],
                        "State": location['region'],
                        "IP": location['ip'],
                        "Count": location['play_count']
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            float(location['lon']), float(location['lat'])
                        ]
                    }
                })

                locs.append({
                    "type": "Feature",
                    "properties": {
                        "geodesic": "true",
                        "geodesic_steps": 50,
                        "geodesic_wrap": "true"
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [float(location['lon']), float(location['lat'])],
                            [float(SERVER_LON), float(SERVER_LAT)],
                        ]
                    }
                })
            except ValueError:
                pass
    return {
        "type": "FeatureCollection",
        "features": locs
    }


def draw_map(map_type, geo_dict, filename, headless, leg_choice):
    import matplotlib as mpl
    if headless:
        mpl.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.basemap import Basemap

    ## Map stuff ##
    plt.figure(figsize=(16, 9), dpi=100, frameon=False)
    lon_r = 0
    lon_l = 0

    if map_type == 'NA':
        m = Basemap(llcrnrlon=-119, llcrnrlat=22, urcrnrlon=-54, urcrnrlat=55, projection='lcc', resolution='l',
                    lat_1=32, lat_2=45, lon_0=-95)
        lon_r = 66.0
        lon_l = -124.0
    elif map_type == 'EU':
        m = Basemap(llcrnrlon=-15., llcrnrlat=20, urcrnrlon=75., urcrnrlat=70, projection='lcc', resolution='l',
                    lat_1=30, lat_2=60, lon_0=35.)
        lon_r = 50.83
        lon_l = -69.03

    elif map_type == 'World':
        m = Basemap(projection='robin', lat_0=0, lon_0=-100, resolution='l', area_thresh=100000.0)
        # m.drawmeridians(np.arange(0, 360, 30))
        # m.drawparallels(np.arange(-90, 90, 30))
        lon_r = 180
        lon_l = -180.0

    # remove line in legend
    mpl.rcParams['legend.handlelength'] = 0
    m.drawmapboundary(fill_color='#1F1F1F')
    m.drawcoastlines()
    m.drawstates()
    m.drawcountries()
    m.drawlsmask(land_color='#3C3C3C', ocean_color='#1F1F1F')

    for key, values in geo_dict.items():
        # add Accuracy as plot/marker size, change play count to del_s value.
        for data in values:
            if key == SERVER_FRIENDLY:
                color = '#FFAC05'
                marker = '*'
                markersize = 10
                zord = 3
                alph = 1
            else:
                if data['platform'] in PLATFORM_COLORS:
                    color = PLATFORM_COLORS[data['platform']]
                else:
                    color = DEFAULT_COLOR
                    print('Platform: {} is missing from PLATFORM_COLORS. Using DEFAULT_COLOR.'.format(data['platform']))
                marker = '.'
                if data['play_count'] >= 100:
                    markersize = (data['play_count'] * .1)
                elif data['play_count'] <= 2:
                    markersize = 2
                else:
                    markersize = 2
                zord = 2
                alph = 0.4
            px, py = m(float(data['lon']), float(data['lat']))
            x, y = m([float(data['lon']), float(SERVER_LON)], [float(data['lat']), float(SERVER_LAT)])
            legend = 'Location: {}, {},  User: {}\nPlatform: {}, IP: {}, Play Count: {}'.format(
                data['city'], data['region'], key, data['platform'], data['ip'], data['play_count'])
            # Keeping lines inside the Location. Plots outside Location will still be in legend

            if float(data['lon']) != float(SERVER_LON) and float(data['lat']) != float(SERVER_LAT) and \
                    lon_l < float(data['lon']) < lon_r:
                # Drawing lines from Server location to client location
                if data['location_count'] > 1:
                    lines = m.plot(x, y, marker=marker, color=color, markersize=0,
                                   label=legend, alpha=.6, zorder=zord, linewidth=2)
                    # Adding dash sequence to 2nd, 3rd, etc lines from same city,state
                    for line in lines:
                        line.set_solid_capstyle('round')
                        dashes = [x * data['location_count'] for x in [5, 8, 5, 8]]
                        line.set_dashes(dashes)

                else:
                    m.plot(x, y, marker=marker, color=color, markersize=0, label=legend, alpha=.4, zorder=zord,
                           linewidth=2)

            m.plot(px, py, marker=marker, color=color, markersize=markersize, label=legend, alpha=alph, zorder=zord)

    if leg_choice:
        handles, labels = plt.gca().get_legend_handles_labels()
        idx = labels.index('Location: {}, {},  User: {}\nPlatform: {}, IP: {}, Play Count: {}'.
                           format(SERVER_CITY, SERVER_STATE, SERVER_FRIENDLY, SERVER_PLATFORM, REPLACEMENT_WAN_IP,
                                  0))
        labels = labels[idx:] + labels[:idx]
        handles = handles[idx:] + handles[:idx]
        by_label = OrderedDict(zip(labels, handles))

        leg = plt.legend(by_label.values(), by_label.keys(), fancybox=True, fontsize='x-small',
                         numpoints=1, title="Legend", labelspacing=1., borderpad=1.5, handletextpad=2.)
        if leg:
            lleng = len(leg.legendHandles)
            for i in range(1, lleng):
                leg.legendHandles[i]._legmarker.set_markersize(10)
                leg.legendHandles[i]._legmarker.set_alpha(1)
            leg.get_title().set_color('#7B777C')
            leg.draggable()
            leg.get_frame().set_facecolor('#2C2C2C')
            for text in leg.get_texts():
                plt.setp(text, color='#A5A5A7')

    plt.title(title_string)
    if filename:
        plt.savefig('{}.png'.format(filename))
        print('Image saved as: {}.png'.format(filename))
    if not headless:
        mng = plt.get_current_fig_manager()
        mng.window.state('zoomed')
        plt.show()


if __name__ == '__main__':

    timestr = time.strftime("%Y%m%d-%H%M%S")
    user_count = get_users_tables()
    user_lst = sorted(get_users_tables('friendly_name', user_count))
    json_check = sorted([f for f in os.listdir('.') if os.path.isfile(f) and f.endswith(".json")],
                        key=os.path.getmtime)
    parser = argparse.ArgumentParser(description="Use PlexPy to draw map of user locations base on IP address.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-m', '--map', default='NA', choices=['NA', 'EU', 'World', 'Geo'], metavar='',
                        help='Map location. choices: (%(choices)s) \n(default: %(default)s)')
    parser.add_argument('-c', '--count', nargs='?', type=int, default=2, metavar='',
                        help='How many IPs to attempt to check. \n(default: %(default)s)')
    parser.add_argument('-u', '--users', nargs='+', type=str, default='all', choices=user_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '%(choices)s \n(default: %(default)s)')
    parser.add_argument('-i', '--ignore', nargs='+', type=str, default=None, choices=user_lst, metavar='',
                        help='Space separated list of case sensitive names to process. Allowed names are: \n'
                             '%(choices)s \n(default: %(default)s)')
    parser.add_argument('-f', '--filename', nargs='+', type=str, default='Map_{}'.format(timestr), metavar='',
                        help='Filename of map. None will not save. \n(default: %(default)s)')
    parser.add_argument('-j', '--json', nargs='?', type=str, choices=json_check, metavar='',
                        help='Filename of json file to use. \n(choices: %(choices)s)')

    parser.add_argument('--headless', action='store_true', help='Run headless.')

    parser.add_argument('--legend', dest='legend', action='store_true', help='Toggle on legend.')
    parser.add_argument('--no_legend', dest='legend', action='store_false', help='Toggle off legend.')
    parser.set_defaults(legend=True)

    opts = parser.parse_args()
    if opts.json:
        if opts.filename == ['None']:
            filename = None
        else:
            filename = '{}'.format(''.join(opts.filename))
        print('Using existing .json file to map.')
        with open(''.join(opts.json)) as json_data:
            geo_json = json.load(json_data)
    else:
        # print(opts)
        if opts.ignore and opts.users == 'all':
            users = [x for x in user_lst if x not in opts.ignore]
        else:
            users = opts.users
        if opts.filename == ['None']:
            filename = None
            json_file = '{}.json'.format(timestr)
        else:
            filename = '{}'.format(''.join(opts.filename))
            json_file = '{}.json'.format(''.join(opts.filename))
        geo_json = get_geo_dict(opts.count, users)
        with open(json_file, 'w') as fp:
            json.dump(geo_json, fp, indent=4, sort_keys=True)

    if opts.map == 'Geo':
        geojson = get_geojson_dict(geo_json)
        print("\n")

        r = requests.post("https://api.github.com/gists",
                          json={
                              "description": title_string,
                              "files": {
                                  '{}.geojson'.format(filename): {
                                      "content": json.dumps(geojson, indent=4)
                                  }
                              }
                          },
                          headers={
                              'Content-Type': 'application/json'
                          })

        print(r.json()['html_url'])
        if not opts.headless:
            webbrowser.open(r.json()['html_url'])
    else:
        draw_map(opts.map, geo_json, filename, opts.headless, opts.legend)
