"""
Delete all playlists from Plex using PlexAPI

https://github.com/mjs7231/python-plexapi
"""

from plexapi.server import PlexServer
import requests

baseurl = 'http://localhost:32400'
token = 'XXXXXXXX'
plex = PlexServer(baseurl, token)

tmp_lst = []


for playlist in plex.playlists():
    tmp = playlist.key
    split = tmp.split('/playlists/')
    tmp_lst += [split[1]]

for i in tmp_lst:
    try:
        r = requests.delete('{}/playlists/{}?X-Plex-Token={}'.format(baseurl,i,token))
        print(r)

    except Exception as e:
        print e
