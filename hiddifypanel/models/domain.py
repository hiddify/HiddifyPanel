from sqlalchemy_serializer import SerializerMixin
from flask import Flask,flash,request
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms import SelectMultipleField
from urllib.parse import urlparse
from .config_enum import ConfigEnum,ConfigCategory
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

class DomainType(StrEnum):
    direct = auto()
    cdn = auto()
    auto_cdn_ip = auto()
    relay = auto()
    fake = auto()
    # worker = auto()
    
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
    sub_link_only= db.Column(db.Boolean,nullable=False,default=False)
    mode = db.Column(db.Enum(DomainType), nullable=False,default=DomainType.direct)
    cdn_ip = db.Column(db.Text(2000), nullable=True,default='')
    # show_all=db.Column(db.Boolean, nullable=True)
    show_domains = db.relationship('Domain', secondary=ShowDomain,
                                primaryjoin=id==ShowDomain.c.domain_id,
                                secondaryjoin=id==ShowDomain.c.related_id, 
                                # backref=backref('show_domains', lazy='dynamic')
                                )
    def __repr__(self):
        return f'{self.domain}'


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



def get_domain(domain):
    return Domain.query.filter(Domain.domain==domain).first()

def get_panel_domains():
    if hconfig(ConfigEnum.is_parent):
        from .parent_domain import ParentDomain
        domains= ParentDomain.query.all()
    else:
        domains=Domain.query.filter(Domain.mode!=DomainType.fake).filter(Domain.sub_link_only==True).all()
        if not len(domains):
            domains=Domain.query.filter(Domain.mode!=DomainType.fake).all()

    if len(domains)==0:
        if request:
            domains=[Domain(domain=request.host)]
        else:
            from hiddifypanel.panel import hiddify
            domains=[Domain(domain=hiddify.get_ip(4))]
    return domains

def get_proxy_domains(domain):
    if hconfig(ConfigEnum.is_parent):
        from hiddifypanel.commercial.parent_domain import ParentDomain
        db_domain=ParentDomain.query.filter(ParentDomain.domain==domain).first() or ParentDomain(domain=domain,show_domains=[])
    else:
        db_domain=Domain.query.filter(Domain.domain==domain).first() or Domain(domain=domain,mode=DomainType.direct,cdn_ip='',show_domains=[])
    return get_proxy_domains_db(db_domain)

def get_proxy_domains_db(db_domain):
    if not db_domain:
        domain=urlparse(request.base_url).hostname
        db_domain=Domain(domain=domain,mode=DomainType.direct,show_domains=[])
        print("no domain")
        flash(_("This domain does not exist in the panel!" + domain))

    return db_domain.show_domains or Domain.query.all()




def get_current_proxy_domains(force_domain=None):
    domain=force_domain or urlparse(request.base_url).hostname
    return get_proxy_domains(domain)