"""
audiobooks /
  -- book1 /
      -- book1 - chapter1.mp3 ...
  -- series1 /
      -- book1 /
          -- book1 - chapter1.mp3 ...
      -- book2 /
          -- book2 - chapter1.mp3 ...

In this structure use series1 to add all the series' books into a colleciton.

"""

from plexapi.server import PlexServer

PLEX_URL = ''
PLEX_TOKEN = ''

plex = PlexServer(PLEX_URL, PLEX_TOKEN)

COLLECTIONAME = 'My Fav Series'
TOPLEVELFOLDERNAME = 'Series Name'
LIBRARYNAME = 'Audio Books'

abLibrary = plex.library.section(LIBRARYNAME)

albums = []
for folder in abLibrary.folders():
    if folder.title == TOPLEVELFOLDERNAME:
        for series in folder.allSubfolders():
            trackKey = series.key
            try:
                track = plex.fetchItem(trackKey)
                albumKey = track.parentKey
                album = plex.fetchItem(albumKey)
                albums.append(album)
            except Exception:
                # print('{} contains additional subfolders that were likely captured. \n[{}].'
                #       .format(series.title, ', '.join([x.title for x in series.allSubfolders()])))
                pass

for album in list(set(albums)):
    print('Adding {} to collection {}.'.format(album.title, COLLECTIONAME))
    album.addCollection(COLLECTIONAME)