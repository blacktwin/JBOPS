# -*- encoding: UTF-8 -*-

'''
https://gist.github.com/blacktwin/f435aa0ccd498b0840d2407d599bf31d
'''

import os
import httplib2

# pip install --upgrade google-api-python-client
from oauth2client.file import Storage
from googleapiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow

import time, shutil, sys

# Copy your credentials from the console
# https://console.developers.google.com
CLIENT_ID = ''
CLIENT_SECRET = ''
OUT_PATH = '' # Output Path



OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
CREDS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')

if not os.path.exists(OUT_PATH):
    os.makedirs(OUT_PATH)

storage = Storage(CREDS_FILE)
credentials = storage.get()

if credentials is None:
    # Run through the OAuth flow and retrieve credentials
    flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI)
    authorize_url = flow.step1_get_authorize_url()
    print('Go to the following link in your browser: ' + authorize_url)
    code = raw_input('Enter verification code: ').strip()
    credentials = flow.step2_exchange(code)
    storage.put(credentials)


# Create an httplib2.Http object and authorize it with our credentials
http = httplib2.Http()
http = credentials.authorize(http)

drive_service = build('drive', 'v2', http=http)

def list_files(service):
    page_token = None
    while True:
        param = {}
        if page_token:
            param['pageToken'] = page_token

        files = service.files().list(**param).execute()
        for item in files['items']:
            yield item
        page_token = files.get('nextPageToken')
        if not page_token:
            break


for item in list_files(drive_service):
    if (item.get('mimeType') == 'image/jpeg' or item.get('mimeType') == 'video/mp4') \
            and (item.get('originalFilename').endswith(('.jpg', '.mp4'))):
        try:
            video_path = OUT_PATH + "\\" + "Video"
            if not os.path.isdir(video_path):
                os.mkdir(video_path)
            picture_path = OUT_PATH + "\\" + "Pictures"
            if not os.path.isdir(picture_path):
                os.mkdir(picture_path)

            if item.get('mimeType') == 'image/jpeg' and item.get('originalFilename').endswith('.jpg'):
                year_date = picture_path + "\\" + item['createdDate'][:4]
            elif item.get('mimeType') == 'video/mp4' and item.get('originalFilename').endswith('.mp4'):
                year_date = video_path + "\\" + item['createdDate'][:4]

            md_date = year_date + "\\" + item['createdDate'][5:10]

            if not os.path.isdir(year_date):
                os.mkdir(year_date)
            if not os.path.isdir(md_date):
                os.mkdir(md_date)
            outfile = os.path.join(md_date, '%s' % item['title'])
            download_url = None
            if 'mimeType' in item and 'image/jpeg' in item['mimeType'] or 'video/mp4' in item['mimeType']:
                download_url = item['downloadUrl']
            else:
                print 'ERROR getting %s' % item.get('title')
                print item
                print dir(item)
            if download_url:
                print "downloading %s" % item.get('title')
                resp, content = drive_service._http.request(download_url)
                if resp.status == 200:
                    if os.path.isfile(outfile):
                        print("ERROR, %s already exist" % outfile)
                    else:
                        with open(outfile, 'wb') as f:
                            f.write(content)
                        print("OK.")
                else:
                    print('ERROR downloading %s' % item.get('title'))
        except Exception as e:
            print(e)
