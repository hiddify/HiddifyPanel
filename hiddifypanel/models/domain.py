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

class DomainType(StrEnum):
    direct = auto()
    cdn = auto()
    relay = auto()
    fake = auto()
    # fake_cdn = "fake_cdn"
    # telegram_faketls = "telegram_faketls"
    # ss_faketls = "ss_faketls"


ShowDomain = db.Table('show_domain',
    db.Column('domain_id', db.Integer, db.ForeignKey('domain.id'), primary_key=True),
    db.Column('related_id', db.Integer, db.ForeignKey('domain.id'), primary_key=True)
)

class Domain(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    child_id= db.Column(db.Integer, db.ForeignKey('child.id'),default=0)
    domain = db.Column(db.String(200), nullable=False, unique=True)
    alias = db.Column(db.String(200))
    mode = db.Column(db.Enum(DomainType), nullable=False)
    cdn_ip = db.Column(db.String(200), nullable=True)
    # show_all=db.Column(db.Boolean, nullable=True)
    show_domains = db.relationship('Domain', secondary=ShowDomain,
                                primaryjoin=id==ShowDomain.c.domain_id,
                                secondaryjoin=id==ShowDomain.c.related_id, 
                                # backref=backref('show_domains', lazy='dynamic')
                                )
    def __repr__(self):
        return f'{self.domain}'
