'''
Download theme songs from Plex TV Shows. Theme songs are mp3 and named by shows as displayed by Plex.
Songs are saved in a 'Theme Songs' directory located in script's path.

'''


from plexapi.server import PlexServer
# pip install plexapi
import os
import re
import urllib

## Edit ##
PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxxx'
TV_LIBRARY = 'TV Shows' # Name of your TV Show library
## /Edit ##

plex = PlexServer(PLEX_URL, PLEX_TOKEN)

# Theme Songs url
themes_url = 'http://tvthemes.plexapp.com/{}.mp3'

# Create /Theme Songs/ directory in same path as script.
out_path = os.path.join(os.path.dirname(__file__), 'Theme Songs')
if not os.path.isdir(out_path):
    os.mkdir(out_path)

# Get episodes from TV Shows
for show in plex.library.section(TV_LIBRARY).all():
    # Remove special characters from name
    filename = '{}.mp3'.format(re.sub('\W+',' ', show.title))
    # Set output path
    theme_path = os.path.join(out_path, filename)
    # Get tvdb_if from first episode, no need to go through all episodes
    tvdb_id = show.episodes()[0].guid.split('/')[2]
    # Download theme song to output path
    urllib.urlretrieve(themes_url.format(tvdb_id), theme_path)
