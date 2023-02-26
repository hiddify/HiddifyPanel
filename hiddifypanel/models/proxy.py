from sqlalchemy_serializer import SerializerMixin
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms import SelectMultipleField

from sqlalchemy.orm import backref

from flask import Markup
from dateutil import relativedelta
from hiddifypanel.panel.database import db
import enum
import datetime
import uuid as uuid_mod
from enum import auto
from strenum import StrEnum


class Proxy(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'),default=0)
    name = db.Column(db.String(200), nullable=False, unique=True)
    enable = db.Column(db.Boolean, nullable=False)
    proto = db.Column(db.String(200), nullable=False)
    l3 = db.Column(db.String(200), nullable=False)
    transport = db.Column(db.String(200), nullable=False)
    cdn = db.Column(db.String(200), nullable=False)
