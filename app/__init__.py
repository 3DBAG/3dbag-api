import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth

logging.basicConfig(level=logging.DEBUG)
# tiles_json = "/data/3DBAGplus/bag_tiles_3k.geojson"
# TILES_SHAPELY= index.read_tiles_to_shapely(tiles_json)
# TILES_RTREE = index.tiles_rtree(TILES_SHAPELY)
app = Flask(__name__)
app.config.from_envvar("APP_CONFIG")
auth = HTTPBasicAuth()
db_users = SQLAlchemy(app)
logging.debug(f"configuration: {app.config}")

from app import views