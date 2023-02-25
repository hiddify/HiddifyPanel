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

ShowDomainParent = db.Table('show_domain_parent',
    db.Column('domain_id', db.Integer, db.ForeignKey('parent_domain.id'), primary_key=True),
    db.Column('related_id', db.Integer, db.ForeignKey('domain.id'), primary_key=True)
)

class ParentDomain(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    domain = db.Column(db.String(200), nullable=False, unique=True)
    show_domains = db.relationship('Domain', secondary=ShowDomainParent,
                                # primaryjoin=id==ShowDomainParent.c.domain_id,
                                # secondaryjoin=id==ShowDomainParent.c.related_id, 
                                backref=backref('parent_domains', lazy='dynamic')
                                )
