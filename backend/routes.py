from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = "172.21.150.156" # os.environ.get('MONGODB_SERVICE')
mongodb_username = 'root'
mongodb_password = "lzmuLlNBIQyGFNk26P6xM7zg" # os.environ.get('MONGODB_PASSWORD')
mongodb_port = 27107

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))



@app.route("/health")
def health():
    return jsonify(dict(status="OK")), 200

@app.route("/count")
def count():
    """return length of data"""
    if songs_list:
        return jsonify(length=len(songs_list)), 200

    return {"message": "Internal server error"}, 500

@app.route("/song")
def songs():
    songs_list = list(db.songs.find({}))
    return {"songs": parse_json(songs_list)}, 200


@app.route("/song/<id>", methods=["GET"])
def get_song_by_id(id: int):
    id = int(id)
    try:
        if id:
            songs_list = list(db.songs.find_one({"id": id}))
            print(songs_list)
            return {"songs": parse_json(songs_list)}, 200
    except:
        return {"message": "song with id not found"}, 404
    

@app.route("/song", methods=["POST"])
def creat_song():
    song = request.get_json()

    if any(s['id'] == song['id'] for s in songs_list):
        return {"message": "Song is already added"}, 302

    songs_list.append(song)
    return jsonify(song), 201

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    song_in = request.get_json()

    song = db.songs.find_one({"id": id})
    if song is None:
        return {"message": "song not found"}, 404

    # Remove MongoDB _id for comparison if present
    song.pop("_id", None)

    if song == song_in:
        return {"message": "song found, but nothing updated"}, 200

    updated_data = {"$set": song_in}
    result = db.songs.update_one({"id": id}, updated_data)

    if result.modified_count == 0:
        return {"message": "song found, but nothing updated"}, 200
    else:
        return {"message": "song updated successfully"}, 201
