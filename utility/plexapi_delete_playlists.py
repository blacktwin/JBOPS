"""
Delete all playlists from Plex using PlexAPI


"""

from plexapi.server import PlexServer

baseurl = 'http://localhost:32400'
token = 'XXXXXXXX'
plex = PlexServer(baseurl, token)


for playlist in plex.playlists():
    playlist.delete()
