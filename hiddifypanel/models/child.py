from __future__ import annotations
import uuid

from sqlalchemy import Column, Integer, String, Enum, text
from enum import auto
from strenum import StrEnum
from flask import g, has_app_context


from hiddifypanel.database import db, db_execute
from sqlalchemy_serializer import SerializerMixin


class ChildMode(StrEnum):
    virtual = auto()
    remote = auto()  # it's child
    parent = auto()

# the child model is node


class Child(db.Model, SerializerMixin):  # type: ignore
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=False)
    mode = Column(Enum(ChildMode), nullable=False, default=ChildMode.virtual)
    # ip = db.Column(db.String(200), nullable=False, unique=True)
    unique_id = Column(String(200), nullable=False, default=lambda: str(uuid.uuid4()), unique=True)
    domains = db.relationship('Domain', cascade="all,delete", backref='child')  # type: ignore
    proxies = db.relationship('Proxy', cascade="all,delete", backref='child')  # type: ignore
    boolconfigs = db.relationship('BoolConfig', cascade="all,delete", backref='child')  # type: ignore
    strconfigs = db.relationship('StrConfig', cascade="all,delete", backref='child')  # type: ignore
    dailyusages = db.relationship('DailyUsage', cascade="all,delete", backref='child')  # type: ignore

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "mode": self.mode,
            "unique_id": self.unique_id
        }

    @staticmethod
    def add_or_update(commit=True, **data) -> Child:
        dbchild = Child.query.filter(Child.id == data['id']).first()
        if not dbchild:
            dbchild = Child()
            db.session.add(dbchild)
        dbchild.name = data['name']
        dbchild.mode = data['mode']
        dbchild.unique_id = data['unique_id']
        if commit:
            db.session.commit()
        return dbchild

    @staticmethod
    def bulk_register(childs, commit=True):
        for child in childs:
            Child.add_or_update(commit=False, **child)
        if commit:
            db.session.commit()

    @classmethod
    def by_id(cls, id: int) -> 'Child':
        return Child.query.filter(Child.id == id).first()

    @classmethod
    def by_unique_id(cls, unique_id: str) -> 'Child':
        return Child.query.filter(Child.unique_id == unique_id).first()

    @classmethod
    def current(cls) -> "Child":
        if has_app_context() and hasattr(g, "child"):
            return g.child
        child = Child.by_id(0)
        if child is None:
            tmp_uuid = str(uuid.uuid4())
            db.session.add(Child(id=0, unique_id=tmp_uuid, name="Root"))
            db.session.commit()
            db_execute(f"update child set id=0 where unique_id='{tmp_uuid}'", commit=True)
            child = Child.by_id(0)

        return child

    @classmethod
    @property
    def node(cls) -> "Child | None":
        if has_app_context() and hasattr(g, "node"):
            return g.node
