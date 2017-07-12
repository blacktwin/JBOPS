from plexapi.server import PlexServer

PLEX_URL = 'http://localhost:32400'
PLEX_TOKEN = 'xxxxx'
plex = PlexServer(PLEX_URL, PLEX_TOKEN)

sections = plex.library.sections()
titles = [titles for libraries in sections for titles in libraries.search('star')]
for title in titles:
    try:
        print(''.join([x.file for x in title.iterParts()]))
    except Exception:
        pass
