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


class Child(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # ip = db.Column(db.String(200), nullable=False, unique=True)
    unique_id = db.Column(db.String(200), nullable=False, unique=True)
    domains = db.relationship('Domain', cascade="all,delete", backref='child')
    proxies = db.relationship('Proxy', cascade="all,delete", backref='child')
    boolconfigs = db.relationship('BoolConfig', cascade="all,delete", backref='child')
    strconfigs = db.relationship('StrConfig', cascade="all,delete", backref='child')
    dailyusages = db.relationship('DailyUsage', cascade="all,delete", backref='child')
