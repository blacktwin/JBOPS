'''
Pull Movie and TV Show poster images from Plex. 
Save to Movie and TV Show directories in scripts working directory.

'''


from plexapi.server import PlexServer
# pip install plexapi
import re
import os
import urllib


PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxxxxx'
plex = PlexServer(PLEX_URL, PLEX_TOKEN)

library_name = ['Movies','TV Shows'] # You library names

# Create paths for Movies and TV Shows inside current directory
movie_path = '{}/Movies'.format(os.path.dirname(__file__))
if not os.path.isdir(movie_path):
    os.mkdir(movie_path)

show_path = '{}/TV Shows'.format(os.path.dirname(__file__))
if not os.path.isdir(show_path):
    os.mkdir(show_path)

child_lst = []

# Get all movies or shows from LIBRARY_NAME
for library in library_name:
    for child in plex.library.section(library).all():
        child_lst.append(child)


for video in child_lst:
    # Clean names of special characters
    name = re.sub('\W+',' ', video.title)
    # Pull URL for poster
    thumb_url = '{}{}?X-Plex-Token={}'.format(PLEX_URL, video.thumb, PLEX_TOKEN)
    if video.type == 'movie':
        image_path = u'{}/{}.jpg'.format(movie_path, name)
        if os.path.isfile(image_path):
            print("ERROR, %s already exist" % image_path)
        else:
            # Save to Movie directory
            urllib.urlretrieve(thumb_url, image_path)
    elif video.type == 'show':
        image_path = u'{}/{}.jpg'.format(show_path, name)
        if os.path.isfile(image_path):
            print("ERROR, %s already exist" % image_path)
        else:
            # Save to TV Show directory
            urllib.urlretrieve(thumb_url, image_path)
