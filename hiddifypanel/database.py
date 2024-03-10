from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import UUIDType
import re
import os

db: SQLAlchemy = SQLAlchemy()
db.UUID = UUIDType  # type: ignore


def init_app(app):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    db.init_app(app)
