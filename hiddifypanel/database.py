from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import UUIDType
import re
import os
from sqlalchemy import Row, text, Sequence


db: SQLAlchemy = SQLAlchemy()
db.UUID = UUIDType  # type: ignore


def init_app(app):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    db.init_app(app)


def db_execute(query: str, return_val: bool = False, commit: bool = False, **params: dict):
    q = db.session.execute(text(query), params)
    if commit:
        db.session.commit()
    if return_val:
        return q.fetchall()

    # with db.engine.connect() as connection:
    #     res = connection.execute(text(query), params)
    #     connection.commit()s
    # return res
