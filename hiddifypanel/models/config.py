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


from .config_enum import ConfigEnum,ConfigCategory
from .domain import DomainType,Domain



class BoolConfig(db.Model, SerializerMixin):
    child_id= db.Column(db.Integer,db.ForeignKey('child.id'), primary_key=True,default=0)
    # category = db.Column(db.String(128), primary_key=True)
    key = db.Column(db.Enum(ConfigEnum), primary_key=True)
    value = db.Column(db.Boolean)


class StrConfig(db.Model, SerializerMixin):
    child_id= db.Column(db.Integer, db.ForeignKey('child.id'), primary_key=True,default=0)
    # category = db.Column(db.String(128), primary_key=True)
    key = db.Column(db.Enum(ConfigEnum), primary_key=True,   default=ConfigEnum.admin_secret)
    value = db.Column(db.String(2048))


def hdomains(mode):
    domains = Domain.query.filter(Domain.mode == mode).all()
    if domains:
        return [d.domain for d in domains]
    return []


def hdomain(mode):
    domains = hdomains(mode)
    if domains:
        return domains[0]
    return None


def get_hdomains():
    return {mode: hdomains(mode) for mode in DomainType}


def hconfig(key: ConfigEnum,child_id=0):
    try:
        str_conf = StrConfig.query.filter(StrConfig.key == key, StrConfig.child_id==child_id).first()
        if str_conf:
            return str_conf.value
        bool_conf = BoolConfig.query.filter(BoolConfig.key == key, BoolConfig.child_id==child_id).first()
        if bool_conf:
            return bool_conf.value
        # if key == ConfigEnum.ssfaketls_fakedomain:
        #     return hdomain(DomainType.ss_faketls)
        # if key == ConfigEnum.telegram_fakedomain:
        #     return hdomain(DomainType.telegram_faketls)
        # if key == ConfigEnum.fake_cdn_domain:
        #     return hdomain(DomainType.fake_cdn)
        print(f'{key} not found ')
    except:
        print(f'{key} error!')

    return None


def set_hconfig(key: ConfigEnum,value,child_id=0,commit=True):
    
        if key.type()==bool:
            dbconf = BoolConfig.query.filter(BoolConfig.key == key, BoolConfig.child_id==child_id).first()    
            if not dbconf:
                dbconf=BoolConfig(key=key,value=value,child_id=child_id)
                db.session.add(dbconf)
        else:
            dbconf = StrConfig.query.filter(StrConfig.key == key, StrConfig.child_id==child_id).first()    
            if not dbconf:
                dbconf=StrConfig(key=key,value=value,child_id=child_id)
                db.session.add(dbconf)
        dbconf.value=value
        if commit:
            db.session.commit()


def get_hconfigs(child_id=0):
    return {**{u.key: u.value for u in BoolConfig.query.filter(BoolConfig.child_id==child_id).all()},
            **{u.key: u.value for u in StrConfig.query.filter(StrConfig.child_id==child_id).all()},
            # ConfigEnum.telegram_fakedomain:hdomain(DomainType.telegram_faketls),
            # ConfigEnum.ssfaketls_fakedomain:hdomain(DomainType.ss_faketls),
            # ConfigEnum.fake_cdn_domain:hdomain(DomainType.fake_cdn)
            }
