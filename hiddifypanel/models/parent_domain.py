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
    alias = db.Column(db.String(200), nullable=False, unique=False)
    show_domains = db.relationship('Domain', secondary=ShowDomainParent,
                                   # primaryjoin=id==ShowDomainParent.c.domain_id,
                                   # secondaryjoin=id==ShowDomainParent.c.related_id,
                                   backref=backref('parent_domains', lazy='dynamic')
                                   )

    def to_dict(d):
        return {
            'domain': d.domain,
            'alias': d.alias,
            'show_domains': [dd.domain for dd in d.show_domains]
        }


def add_or_update_parent_domains(commit=True, **parent_domain):
    dbdomain = ParentDomain.query.filter(ParentDomain.domain == parent_domain['domain']).first()
    if not dbdomain:
        dbdomain = ParentDomain(domain=parent_domain['domain'])
        db.session.add(dbdomain)
    show_domains = parent_domain.get('show_domains', [])
    dbdomain.show_domains = Domain.query.filter(Domain.domain.in_(show_domains)).all()
    dbdomain.alias = parent_domain.get('alias')
    if commit:
        db.session.commit()


def bulk_register_parent_domains(parent_domains, commit=True, remove=False):
    for p in parent_domains:
        add_or_update_parent_domains(commit=False, **p)
    if remove:
        dd = {p.domain: 1 for p in parent_domains}
        for d in ParentDomain.query.all():
            if d.domain not in dd:
                db.session.delete(d)
    if commit:
        db.session.commit()
