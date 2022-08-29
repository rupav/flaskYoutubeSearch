from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from Models.video import db, connect_to_db, Video, Thumbnail
import os, gc
from datetime import datetime
from search import youtube_search, get_next_page_token
from utils.constants import YOUTUBE_SEARCH_REQUEST_PARAMS_VALUES, API_CALL_COUNT, YOUTUBE_VIDEO_URL_PREFIX
from utils.scheduler import schedule

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
file_path = os.path.abspath(os.getcwd())+"/DataBase/test.db"
_database = 'sqlite:///'+file_path

connect_to_db(app, _database)

@app.route("/")
def hello():
  return {
    "paths": {
      "/save": "Populates the DB from youtube videos data - calls the API API_CALL_COUNT times, and commits in the DB same no. of times. This limit to prevent exhasting of API Key for the user",
      "/get": "accepts query params 'page_number' and 'page_size', returns paginated response of the stored videos data in reverse chronological order",
      "/search": "accepts query params 'title' and 'desc', returns list of the videos with either of the matching query params"
    }
  }

def get_items(search_response):
  items = []
  for search_result in search_response.get('items', []):
    item = {}
    item['title'] = search_result['snippet']['title']
    item['published_at'] = search_result['snippet']['publishedAt']
    item['desc'] = search_result['snippet']['description']
    item['thumbnails'] = search_result['snippet']['thumbnails']
    item['id'] = search_result['id']['videoId']
    items.append(item)
  return items

def store_in_db(items):
  try:
    for item in items:
      if (Video.query.filter_by(vid = item['id']).first() != None):
        # Since Youtube Search returns results in chronological reverse order, and we are saving the data in same order,
        # if we find another video with same ID while updating the DB async, all next videos from Youtube search are already stored in our DB
        print('Video is already stored in DB: ', item['id'])
        db.session.commit()
        return False
      video_row = Video(vid = item['id'], published_at = datetime.fromisoformat(item['published_at'][:-1]), title = item['title'], desc = item['desc'])
      db.session.add(video_row)
      for key in item['thumbnails']:
        thumbnail_data = item['thumbnails'][key]
        thumbnail_row = Thumbnail(vid = item['id'], type = key,  url = thumbnail_data['url'], height = thumbnail_data['height'], width = thumbnail_data['width'])
        db.session.add(thumbnail_row)
    db.session.commit()
    return True
  except Exception as e:
    print('Exception occured while saving video data in DB is', e)
    return False

@app.route("/save")
def save_videos_data():
  """Populate the DB from youtube videos data"""
  try:
    request_params = {}
    request_params['q'] = YOUTUBE_SEARCH_REQUEST_PARAMS_VALUES['QUERY']
    request_params['part'] = YOUTUBE_SEARCH_REQUEST_PARAMS_VALUES['PART']
    request_params['type'] = YOUTUBE_SEARCH_REQUEST_PARAMS_VALUES['TYPE']
    request_params['order'] = YOUTUBE_SEARCH_REQUEST_PARAMS_VALUES['ORDER_BY']
    request_params['maxResults'] = YOUTUBE_SEARCH_REQUEST_PARAMS_VALUES['MAX_RESULTS']
    request_params['publishedAfter'] = YOUTUBE_SEARCH_REQUEST_PARAMS_VALUES['PUBLISHED_AFTER']

    db.create_all()

    next_page_token = None
    for _ in range(API_CALL_COUNT):
      request_params['pageToken'] = next_page_token
      search_resp = youtube_search(request_params)
      items = get_items(search_resp)
      next_page_token = get_next_page_token(search_resp)
      db_success = store_in_db(items)
      if (next_page_token == None or db_success == False):
        break

    db.session.close()
    gc.collect()
    return 'DB Save is completed'
  except Exception as e:
    print('Failed due to: ', e)
    return 'DB Save failed'

def getVideoRespObj(videos_db_result):
  videos = []
  for video_row in videos_db_result:
    video_obj = {}
    video_obj['title'] = video_row.title
    video_obj['url'] = YOUTUBE_VIDEO_URL_PREFIX + video_row.vid
    video_obj['desc'] = video_row.desc
    video_obj['publishedAt'] = video_row.published_at
    video_obj['thumbnails'] = []
    thumbnails_db_result = Thumbnail.query.filter_by(vid = video_row.vid).all()
    for thumbnail_row in thumbnails_db_result:
      thumbnail_obj = {}
      thumbnail_obj['type'] = thumbnail_row.type
      thumbnail_obj['url'] = thumbnail_row.url
      thumbnail_obj['width'] = thumbnail_row.width
      thumbnail_obj['height'] = thumbnail_row.height
      video_obj['thumbnails'].append(thumbnail_obj)
    videos.append(video_obj)
  return videos

@app.route("/get")
def get_paginated_videos_response():
  """accepts query params 'page_number' and 'page_size', returns paginated response of the stored videos data in reverse chronological order"""
  args = request.args
  page_number = args.get('page_number', type=int, default=0)
  page_size = args.get('page_size', type=int, default=1)
  
  # Find in DB Top 'page_size' results with offset 'page_number' x 'page_size'
  offset =  page_number * page_size
  videos_db_result = Video.query.order_by(Video.published_at.desc()).offset(offset).limit(page_size).all()
  resp = {
    'videos': getVideoRespObj(videos_db_result),
    'success': True
  }
  return resp

@app.get("/search")
def search():
  """accepts query params 'title' and 'desc', returns list of the videos with either of the matching query params"""
  args = request.args
  search_by_title = args.get('title')
  search_by_desc = args.get('desc')
  resp = {
    'videos': [],
    'success': True
  }
  if (search_by_title is not None):
    videos_db_result = Video.query.filter(Video.title.like("%" + search_by_title + "%")).all()
    resp['videos'] = getVideoRespObj(videos_db_result)
  elif (search_by_desc is not None):
    videos_db_result = Video.query.filter(Video.desc.like("%" + search_by_desc + "%")).all()
    resp['videos'] = getVideoRespObj(videos_db_result)
  return resp

# db.drop_all() # Clear the DB
schedule(save_videos_data)

if __name__ == "__main__":
  db.create_all()
  app.run()
