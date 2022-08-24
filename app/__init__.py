import logging
from sys import getsizeof

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from app import parser

logging.basicConfig(level=logging.DEBUG)
# tiles_json = "/data/3DBAGplus/bag_tiles_3k.geojson"
# TILES_SHAPELY= index.read_tiles_to_shapely(tiles_json)
# TILES_RTREE = index.tiles_rtree(TILES_SHAPELY)
app = Flask(__name__)
app.config.from_envvar("APP_CONFIG")
auth = HTTPBasicAuth()
db_users = SQLAlchemy(app)
logging.debug(f"configuration: {app.config}")
FEATURE_IDX = parser.feature_index(app.config["FEATURE_INDEX_CSV"]) # feature index of (featureId : tile_id)
logging.debug(f"memory size of FEATURE_IDX from json: {getsizeof(FEATURE_IDX)} bytes")
FEATURE_IDS = list(FEATURE_IDX.keys()) # featureID list

from app import views