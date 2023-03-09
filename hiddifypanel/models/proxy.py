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


class ProxyTransport(StrEnum):
    grpc=auto()
    XTLS=auto()
    faketls=auto()
    shadowtls=auto()
    # h1=auto()
    WS=auto()
    tcp=auto()

class ProxyCDN(StrEnum):
    CDN=auto()
    direct=auto()
    Fake=auto()
class ProxyProto(StrEnum):
    vless=auto()
    trojan=auto()
    vmess=auto()
    ss=auto()
    v2ray=auto()
    ssr=auto()
class ProxyL3(StrEnum):
    tls=auto()
    tls_h2=auto()
    tls_h2_h1=auto()
    http=auto()
    kcp=auto()

class Proxy(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'),default=0)
    name = db.Column(db.String(200), nullable=False, unique=True)
    enable = db.Column(db.Boolean, nullable=False)
    proto = db.Column(db.Enum(ProxyProto), nullable=False)
    l3 = db.Column(db.Enum(ProxyL3), nullable=False)
    transport = db.Column(db.Enum(ProxyTransport), nullable=False)
    cdn = db.Column(db.Enum(ProxyCDN), nullable=False)
