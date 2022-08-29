#!/usr/bin/python
import argparse
import os

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


DEVELOPER_KEY = os.environ.get('DEVELOPER_KEY')
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

def get_next_page_token(search_response):
  return search_response.get('nextPageToken', None)

def youtube_search(options):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)
  # Call the search.list method to retrieve results matching the specified
  # query term.
  search_response = youtube.search().list(**options).execute()
  return search_response


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--q', help='Search term', default='Google')
  parser.add_argument('--max-results', help='Max results', default=25)
  parser.add_argument('--publishedAfter', help='Published After DateTime', default='2022-08-20T00:00:00Z')
  args = parser.parse_args()

  try:
    youtube_search(args)
  except HttpError as e:
    print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
