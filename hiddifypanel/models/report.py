from sqlalchemy_serializer import SerializerMixin
from flask import Flask, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms import SelectMultipleField
from urllib.parse import urlparse
from .config_enum import ConfigEnum, ConfigCategory
from .config import hconfig

from sqlalchemy.orm import backref

from flask import Markup
from dateutil import relativedelta
from hiddifypanel.panel.database import db

import enum
import datetime
import uuid as uuid_mod
from enum import auto
from strenum import StrEnum


class Report(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), default=0, nullable=False)
    asn_id = db.Column(db.String(200), nullable=False, unique=False)
    city = db.Column(db.String(200))
    country = db.Column(db.String(200))
    latitude = Column(Float,)
    longitude = Column(Float, )
    accuracy_radius = Column(Float, )
    
    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.min)
    details = db.relationship('ReportDetail', cascade="all,delete", backref='report',    lazy='dynamic',)


class ReportDetail(db.Model, SerializerMixin):
    report_id = db.Column(db.Integer, db.ForeignKey('report.id'), primary_key=True, )
    proxy_id = db.Column(db.Integer, db.ForeignKey('proxy.id'), primary_key=True, )
    ping = db.Column(db.Integer, default=-1)
