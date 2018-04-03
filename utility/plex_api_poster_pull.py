"""
Description: Pull Movie and TV Show poster images from Plex.  Save to Movie and TV Show directories in scripts working directory.
Author: Blacktwin
Requires: plexapi

 Example:
    python plex_api_poster_pull.py

"""


from plexapi.server import PlexServer
import re
import os
import urllib


PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = ''
plex = PlexServer(PLEX_URL, PLEX_TOKEN)

library_name = ['Movies','TV Shows'] # You library names

# Create paths for Movies and TV Shows inside current directory
movie_path = '{}/Movies'.format(os.path.dirname(__file__))
if not os.path.isdir(movie_path):
    os.mkdir(movie_path)

show_path = '{}/TV Shows'.format(os.path.dirname(__file__))
if not os.path.isdir(show_path):
    os.mkdir(show_path)


# Get all movies or shows from LIBRARY_NAME
for library in library_name:
    for child in plex.library.section(library).all():
        # Clean names of special characters
        name = re.sub('\W+',' ', child.title)
        # Add (year) to name
        name = '{} ({})'.format(name, child.year)
        # Pull URL for poster
        thumb_url = '{}{}?X-Plex-Token={}'.format(PLEX_URL, child.thumb, PLEX_TOKEN)
        # Select path based on media_type
        if child.type == 'movie':
            image_path = u'{}/{}.jpg'.format(movie_path, name)
        elif child.type == 'show':
            image_path = u'{}/{}.jpg'.format(show_path, name)
        # Check if file already exists
        if os.path.isfile(image_path):
            print("ERROR, %s already exist" % image_path)
        else:
            # Save to directory
            urllib.urlretrieve(thumb_url, image_path)
