from plexapi.server import PlexServer
import requests
import xml.etree.ElementTree as ET
#import pdb             //enable for debugging
#pdb.set_trace()       //insert where to start debugging, press n to proceed to next line

#This python script will set all movies and shows in your local Plex library to English non forced subtitles by default. The subtitle selections will apply to your Plex profile and be remembered on other devices.

# Connect to the Plex server
baseurl = 'http://localhost:32400'
token = 'xxxxxxxx'
plex = PlexServer(baseurl, token)


# Set all movies to use English non-forced subtitles if available, otherwise print no subtitles found
for movie in plex.library.section('Movies').all():
    movie.reload()
    english_subs = [stream for stream in movie.subtitleStreams() if stream.languageCode == 'eng']
    non_forced_english_subs = [stream for stream in english_subs if not stream.forced]
    forced_english_subs = [stream for stream in english_subs if stream.forced]
    part = movie.media[0].parts[0]
    partsid = part.id
    if forced_english_subs and non_forced_english_subs:
        # If movies has forced english subs AND non forced english subs THEN set show to prefer english non forced subs
        # Send a request to the Plex client to set the subtitle stream
        url = f'{baseurl}/library/parts/{partsid}?subtitleStreamID={non_forced_english_subs[0].id}&allParts=1'
        headers = {'X-Plex-Token': token}
        requests.put(url, headers=headers)
        print(f'{movie.title}: Setting non forced English subtitles.')
    elif non_forced_english_subs and not forced_english_subs:
        print(f'{movie.title}: Has english subtitles but no english forced subtitles. No subtitle changes.')
    elif not non_forced_english_subs and not forced_english_subs and not forced_english_subs:
        print(f'{movie.title}: No English subtitles found. No subtitle changes.')
    else:
        print(f'{movie.title}: No subtitle changes.')


# Set all TV shows to use English non-forced subtitles if available, otherwise print no subtitles found
for show in plex.library.section('TV Shows').all():
    show.reload()
    for episode in show.episodes():
        show.reload()
        episode.reload()
        english_subs = [stream for stream in episode.subtitleStreams() if stream.languageCode == 'eng']
        non_forced_english_subs = [stream for stream in english_subs if not stream.forced]
        forced_english_subs = [stream for stream in english_subs if stream.forced]
        part = episode.media[0].parts[0]
        partsid = part.id
        if forced_english_subs and non_forced_english_subs:
            # If show has forced english subs AND non forced english subs THEN set show to prefer english non forced subs
            # Send a request to the Plex client to set the subtitle stream
            url = f'{baseurl}/library/parts/{partsid}?subtitleStreamID={non_forced_english_subs[0].id}&allParts=1'
            headers = {'X-Plex-Token': token}
            requests.put(url, headers=headers)
            print(f'{show.title} - {episode.title}: Setting non forced English subtitles.')
        elif non_forced_english_subs and not forced_english_subs:
            print(f'{show.title} - {episode.title}: Has english subtitles but no english forecd subtitles. No subtitle changes.')
        elif not non_forced_english_subs and not forced_english_subs and not forced_english_subs:
            print(f'{show.title} - {episode.title}: No English subtitles found. No subtitle changes.')
        else:
            print(f'{show.title} - {episode.title}: No subtitle changes.')


input("Press [Enter] to continue.")      #//enable to stop window from closing on completion
