#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Description:  Automatically change episode artwork in Plex to hide spoilers.
# Author:       /u/SwiftPanda16
# Requires:     plexapi, requests
# Tautulli script trigger:
#    * Notify on recently added
#    * Notify on watched (optional - to remove the artwork after being watched)
# Tautulli script conditions:
#    * Condition {1}:
#        [Media Type | is | show or season or episode]
#    * Condition {2} (optional):
#        [ Library Name | is | DVR ]
#        [ Show Namme | is | Game of Thrones ]
# Tautulli script arguments:
#    * Recently Added:
#        To use an image file (can be image in the same directory as this script, or full path to an image):
#            --rating_key {rating_key} --image spoilers.png
#        To blur the episode artwork (optional blur in pixels):
#            --rating_key {rating_key} --blur 25
#        To add a prefix to the summary (optional string prefix):
#            --rating_key {rating_key} --summary_prefix "** SPOILERS **"
#        To upload the episode artwork instead of creating a local asset (optional, for when the script cannot access the media folder):
#            --rating_key {rating_key} --blur 25 --upload
#    * Watched (optional):
#        To remove the local asset episode artwork:
#            --rating_key {rating_key} --remove
#        To remove the uploaded episode artwork
#            --rating_key {rating_key} --remove --upload
# Note:
#    * "Use local assets" must be enabled for the library in Plex (Manage Library > Edit > Advanced > Use local assets).

import argparse
import os
import requests
import shutil
from plexapi.server import PlexServer

PLEX_URL = ''
PLEX_TOKEN = ''

# Environmental Variables
PLEX_URL = os.getenv('PLEX_URL', PLEX_URL)
PLEX_TOKEN = os.getenv('PLEX_TOKEN', PLEX_TOKEN)


def modify_episode_artwork(plex, rating_key, image=None, blur=None, summary_prefix=None, remove=False, upload=False):
    item = plex.fetchItem(rating_key)

    if item.type == 'show':
        episodes = item.episodes()
    elif item.type == 'season':
        episodes = item.episodes()
    elif item.type == 'episode':
        episodes = [item]
    else:
        print('Only media type show, season, or episode is supported: '
              '{item.title} ({item.ratingKey}) is media type {item.type}.'.format(item=item))
        return

    for episode in episodes:
        for part in episode.iterParts():
            episode_filepath = part.file
            episode_folder = os.path.dirname(episode_filepath)
            episode_filename = os.path.splitext(os.path.basename(episode_filepath))[0]

            if remove:
                if upload:
                    # Unlock and select the first poster
                    episode.unlockPoster().posters()[0].select()
                else:
                    # Find image files with the same name as the episode
                    for filename in os.listdir(episode_folder):
                        if filename.startswith(episode_filename) and filename.endswith(('.jpg', '.png')):
                            # Delete the episode artwork image file
                            os.remove(os.path.join(episode_folder, filename))

                # Unlock the summary so it will get updated on refresh
                episode.editSummary(episode.summary, locked=False)
                continue

            if image:
                if upload:
                    # Upload the image to the episode artwork
                    episode.uploadPoster(filepath=image)
                else:
                    # File path to episode artwork using the same episode file name
                    episode_artwork = os.path.splitext(episode_filepath)[0] + os.path.splitext(image)[1]
                    # Copy the image to the episode artwork
                    shutil.copy2(image, episode_artwork)

            elif blur:
                # File path to episode artwork using the same episode file name
                episode_artwork = os.path.splitext(episode_filepath)[0] + '.png'
                # Get the blurred artwork
                image_url = plex.transcodeImage(
                    episode.thumbUrl,
                    height=270,
                    width=480,
                    blur=blur,
                    imageFormat='png'
                )
                r = requests.get(image_url, stream=True)
                if r.status_code == 200:
                    r.raw.decode_content = True
                    if upload:
                        # Upload the image to the episode artwork
                        episode.uploadPoster(filepath=r.raw)
                    else:
                        # Copy the image to the episode artwork
                        with open(episode_artwork, 'wb') as f:
                            shutil.copyfileobj(r.raw, f)

            if summary_prefix and not episode.summary.startswith(summary_prefix):
                # Use a zero-width space (\u200b) for blank lines
                episode.editSummary(summary_prefix + '\n\u200b\n' + episode.summary)

        # Refresh metadata for the episode
        episode.refresh()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--rating_key', required=True, type=int)
    parser.add_argument('--image')
    parser.add_argument('--blur', type=int, default=25)
    parser.add_argument('--summary_prefix', nargs='?', const='** SPOILERS **')
    parser.add_argument('--remove', action='store_true')
    parser.add_argument('--upload', action='store_true')
    opts = parser.parse_args()

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    modify_episode_artwork(plex, **vars(opts))
