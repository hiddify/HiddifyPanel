from __future__ import annotations
import uuid as uuid_mod
from sqlalchemy_serializer import SerializerMixin
from enum import auto
from strenum import StrEnum

from hiddifypanel.panel.database import db


class ChildMode(StrEnum):
    virtual = auto()
    remote = auto()


class Child(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    mode = db.Column(db.Enum(ChildMode), nullable=False, default=ChildMode.virtual)
    # ip = db.Column(db.String(200), nullable=False, unique=True)
    unique_id = db.Column(db.String(200), nullable=False, default=lambda: str(uuid_mod.uuid4()), unique=True)
    domains = db.relationship('Domain', cascade="all,delete", backref='child')
    proxies = db.relationship('Proxy', cascade="all,delete", backref='child')
    boolconfigs = db.relationship('BoolConfig', cascade="all,delete", backref='child')
    strconfigs = db.relationship('StrConfig', cascade="all,delete", backref='child')
    dailyusages = db.relationship('DailyUsage', cascade="all,delete", backref='child')

    @classmethod
    def by_id(cls, id: int) -> Child:
        return Child.query.filter(Child.id == id).first()
