from hiddifypanel.cache import cache
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
from hiddifypanel import Events

from .config_enum import ConfigEnum, ConfigCategory


class BoolConfig(db.Model, SerializerMixin):
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), primary_key=True, default=0)
    # category = db.Column(db.String(128), primary_key=True)
    key = db.Column(db.Enum(ConfigEnum), primary_key=True)
    value = db.Column(db.Boolean)

    def to_dict(d):
        return {
            'key': d.key,
            'value': d.value,
            'child_unique_id': d.child.unique_id if d.child else ''
        }


class StrConfig(db.Model, SerializerMixin):
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), primary_key=True, default=0)
    # category = db.Column(db.String(128), primary_key=True)
    key = db.Column(db.Enum(ConfigEnum), primary_key=True, default=ConfigEnum.admin_secret)
    value = db.Column(db.String(2048))

    def to_dict(d):
        return {
            'key': d.key,
            'value': d.value,
            'child_unique_id': d.child.unique_id if d.child else ''
        }


@cache.cache(ttl=500)
def hconfig(key: ConfigEnum, child_id=0):
    value = None
    try:
        str_conf = StrConfig.query.filter(StrConfig.key == key, StrConfig.child_id == child_id).first()
        if str_conf:
            value = str_conf.value
        else:
            bool_conf = BoolConfig.query.filter(BoolConfig.key == key, BoolConfig.child_id == child_id).first()
            if bool_conf:
                value = bool_conf.value
            else:
                # if key == ConfigEnum.ssfaketls_fakedomain:
                #     return hdomain(DomainType.ss_faketls)
                # if key == ConfigEnum.telegram_fakedomain:
                #     return hdomain(DomainType.telegram_faketls)
                # if key == ConfigEnum.fake_cdn_domain:
                #     return hdomain(DomainType.fake_cdn)
                print(f'{key} not found ')
    except:
        print(f'{key} error!')
        raise

    return value


def set_hconfig(key: ConfigEnum, value, child_id=0, commit=True):
    # hconfig.invalidate(key, child_id)
    # get_hconfigs.invalidate(child_id)
    hconfig.invalidate(key, child_id)
    hconfig.invalidate(key, child_id=child_id)
    hconfig.invalidate(key=key, child_id=child_id)
    if child_id == 0:
        hconfig.invalidate(key)
    # hconfig.invalidate_all()
    get_hconfigs.invalidate_all()
    if key.type() == bool:
        dbconf = BoolConfig.query.filter(BoolConfig.key == key, BoolConfig.child_id == child_id).first()
        if not dbconf:
            dbconf = BoolConfig(key=key, value=value, child_id=child_id)
            db.session.add(dbconf)
    else:
        dbconf = StrConfig.query.filter(StrConfig.key == key, StrConfig.child_id == child_id).first()
        if not dbconf:
            dbconf = StrConfig(key=key, value=value, child_id=child_id)
            db.session.add(dbconf)
    old_v = dbconf.value
    dbconf.value = value
    Events.config_changed.notify(conf=dbconf, old_value=old_v)
    if commit:
        db.session.commit()


@cache.cache(ttl=500)
def get_hconfigs(child_id=0):
    return {**{u.key: u.value for u in BoolConfig.query.filter(BoolConfig.child_id == child_id).all()},
            **{u.key: u.value for u in StrConfig.query.filter(StrConfig.child_id == child_id).all()},
            # ConfigEnum.telegram_fakedomain:hdomain(DomainType.telegram_faketls),
            # ConfigEnum.ssfaketls_fakedomain:hdomain(DomainType.ss_faketls),
            # ConfigEnum.fake_cdn_domain:hdomain(DomainType.fake_cdn)
            }


def add_or_update_config(commit=True, child_id=0, override_unique_id=True, **config):
    print(config)
    c = config['key']
    ckey = ConfigEnum(c)
    if c == ConfigEnum.unique_id and not override_unique_id:
        return

    v = str(config['value']).lower() == "true" if ckey.type() == bool else config['value']
    if ckey in [ConfigEnum.db_version]:
        return
    set_hconfig(ckey, v, child_id, commit=commit)


def bulk_register_configs(hconfigs, commit=True, override_child_id=None, override_unique_id=True):
    from hiddifypanel.panel import hiddify
    for conf in hconfigs:
        # print(conf)
        if conf['key'] == ConfigEnum.unique_id and not override_unique_id:
            continue
        child_id = override_child_id if override_child_id is not None else hiddify.get_child(conf.get('child_unique_id', None))
        # print(conf)
        add_or_update_config(commit=False, child_id=child_id, **conf)
    if commit:
        db.session.commit()
