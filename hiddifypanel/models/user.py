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

class UserMode(StrEnum):
    no_reset = auto()
    monthly = auto()
    weekly = auto()
    daily = auto()
    disable = auto()


class User(db.Model, SerializerMixin):
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), default=lambda: str(uuid_mod.uuid4()), nullable=False, unique=True)
    name = db.Column(db.String(512), nullable=False)
    last_online=db.Column(db.DateTime,nullable=False,default=datetime.datetime.min)
    expiry_time = db.Column(db.Date, default=datetime.date.today() + relativedelta.relativedelta(months=6))
    usage_limit_GB = db.Column(db.Numeric(6, 9, asdecimal=False), default=1000, nullable=False)
    package_days=db.Column(db.Integer,default=90)
    mode=db.Column(db.Enum(UserMode),default=UserMode.no_reset)
    monthly=db.Column(db.Boolean,default=False)

    start_date=db.Column(db.Date,nullable=True)

    current_usage_GB = db.Column(db.Numeric(6, 9, asdecimal=False), default=0, nullable=False)
    last_reset_time = db.Column(db.Date, default=datetime.date.today())
    comment = db.Column(db.String(512))


def is_user_active(u):
    if u.mode==UserMode.disable:
        return False
    if u.usage_limit_GB<u.current_usage_GB:
        return False
    if remaining_days(u)<0:
        return False
    return True
    

def remaining_days(u):
    if u.start_date:
        return u.package_days-(datetime.date.today()-u.start_date).days
    return u.package_days


package_mode_dic={
        UserMode.daily:1,
        UserMode.weekly:7,
        UserMode.monthly:30
}
def days_to_reset(user):
    if user.start_date:
        return package_mode_dic.get(user.mode,10000)-(datetime.date.today()-user.start_date).days % package_mode_dic.get(user.mode,10000)
    return package_mode_dic.get(user.mode,10000)