"""
Copyright (c) 2023 TU Delft 3D geoinformation group, Ravi Peters (3DGI), and Balázs Dukai (3DGI)
"""

from app import db_users, auth
from enum import Enum
from werkzeug.security import check_password_hash, generate_password_hash
from flask import g


class Permission(Enum):
    USER = 1
    ADMINISTRATOR = 16


class UserAuth(db_users.Model):
    __tablename__ = "userauth"

    id = db_users.Column(db_users.Integer, primary_key=True)
    username = db_users.Column(db_users.String(80),
                               unique=True,
                               nullable=False)
    # TODO: We should probably generate the API keys with os.urandom(24)
    # as per https://realpython.com/token-based-authentication-with-flask/
    password_hash = db_users.Column(db_users.String(128), nullable=False)
    role = db_users.Column(db_users.Enum(Permission))

    def __init__(self, username, password, role=Permission.USER):
        self.username = username
        # TODO: require at least 12 mixed character long password
        self.password = password
        self.role = role

    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256:320000")

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_roles(self):
        return self.role


@auth.get_user_roles
def get_user_roles(user):
    return user.get_roles()


@auth.verify_password
def verify_password(username, password):
    if username == "":
        return None
    existing_user = UserAuth.query.filter_by(username=username).first()
    if not existing_user:
        return None
    g.current_user = username
    if existing_user.verify_password(password):
        return existing_user
