import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config.from_envvar("APP_CONFIG")
auth = HTTPBasicAuth()
db_users = SQLAlchemy(app)
logging.debug(f"configuration: {app.config}")

from app import views