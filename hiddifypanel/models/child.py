from __future__ import annotations
import uuid
from sqlalchemy_serializer import SerializerMixin
from enum import auto
from strenum import StrEnum
from flask import g, has_app_context


from hiddifypanel.database import db


class ChildMode(StrEnum):
    virtual = auto()
    remote = auto()


class Child(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    mode = db.Column(db.Enum(ChildMode), nullable=False, default=ChildMode.virtual)
    # ip = db.Column(db.String(200), nullable=False, unique=True)
    unique_id = db.Column(db.String(200), nullable=False, default=lambda: str(uuid.uuid4()), unique=True)
    domains = db.relationship('Domain', cascade="all,delete", backref='child')
    proxies = db.relationship('Proxy', cascade="all,delete", backref='child')
    boolconfigs = db.relationship('BoolConfig', cascade="all,delete", backref='child')
    strconfigs = db.relationship('StrConfig', cascade="all,delete", backref='child')
    dailyusages = db.relationship('DailyUsage', cascade="all,delete", backref='child')

    @classmethod
    def by_id(cls, id: int) -> "Child":
        return Child.query.filter(Child.id == id).first()

    @classmethod
    @property
    def current(cls) -> "Child":
        if has_app_context() and hasattr(g, "child"):
            return g.child
        child= Child.by_id(0)
        if child is None:
            tmp_uuid = str(uuid.uuid4())
            db.session.add(Child(id=0,unique_id=tmp_uuid, name="Root"))
            db.session.commit()
            db.engine.execute(f'update child set id=0 where unique_id="{tmp_uuid}"')
            child=Child.by_id(0)
        return child
