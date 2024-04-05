from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import UUIDType
import re
import os
from sqlalchemy import text


db: SQLAlchemy = SQLAlchemy()
db.UUID = UUIDType  # type: ignore


def init_app(app):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    db.init_app(app)


def db_execute(query: str, **params: dict):
    with db.engine.connect() as connection:
        res = connection.execute(text(query), params)
        connection.commit()
        return res
