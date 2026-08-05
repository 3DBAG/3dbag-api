"""
Copyright (c) 2023 TU Delft 3D geoinformation group, Ravi Peters (3DGI), and Balázs Dukai (3DGI)
"""

import logging
import os

from flask import Flask
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["POSTGRES_URL"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = False

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

auth = HTTPBasicAuth()
db_users = SQLAlchemy(app)

from app import errors, views  # noqa: E402, F401
