import datetime
import uuid
from hiddifypanel.models.role import Role
from sqlalchemy import Column, String, BigInteger, Enum

from flask_login import UserMixin as FlaskLoginUserMixin
from hiddifypanel.models import Lang
from hiddifypanel.database import db
from sqlalchemy_serializer import SerializerMixin


class BaseAccount(db.Model, SerializerMixin, FlaskLoginUserMixin):  # type: ignore
    __abstract__ = True
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), nullable=False, unique=True, index=True)
    name = Column(String(512), nullable=False, default='')
    username = Column(String(100), nullable=True, default='', index=True)
    password = Column(String(100), nullable=True, default='')
    comment = Column(String(512), nullable=True, default='')
    telegram_id = Column(BigInteger, nullable=True, default=None, index=True)
    lang = Column(Enum(Lang), default=None)

    @property
    def role(self) -> Role | None:
        return None

    def get_id(self) -> str | None:
        return f'{self.__class__.name}_{self.id if self.hasattr("id") else "-"}'

    def is_username_unique(self) -> bool:
        cls = self.__class__()
        model = cls.query.filter(cls.username == self.username, cls.id != self.id).first()
        if model:
            return False
        return True

    def to_dict(self, convert_date=True) -> dict:
        return {
            'name': self.name,
            'comment': self.comment,
            'uuid': self.uuid,
            'telegram_id': self.telegram_id,
            'lang': self.lang
        }

    @classmethod
    def by_id(cls, id: int):
        # return cls.query.filter(cls.id == id).first()
        return cls.query.get(id)

    @classmethod
    def by_uuid(cls, uuid: str, create: bool = False):
        if not isinstance(uuid, str):
            uuid = str(uuid)
        account = cls.query.filter(cls.uuid == uuid).first()
        if not account and create:
            raise NotImplementedError
        return account

    @classmethod
    def by_username_password(cls, username: str, password: str):
        return cls.query.filter(cls.username == username, cls.password == password).first()

    @classmethod
    def add_or_update(cls, commit: bool = True, old_uuid=None, **data):
        db_account: BaseAccount = cls.by_uuid(old_uuid or data.get('uuid'), create=True)
        from hiddifypanel import hutils
        if hutils.auth.is_uuid_valid(data.get('uuid')):
            db_account.uuid = data['uuid']

        if data.get('name') is not None:
            db_account.name = data.get('name')

        if data.get('comment') is not None:
            db_account.comment = data.get('comment')
        if data.get('telegram_id') is not None:
            db_account.telegram_id = hutils.convert.to_int(data.get('telegram_id'))
        if data.get('lang') is not None:
            db_account.lang = data.get('lang')
        if commit:
            db.session.commit()  # type: ignore
        return db_account

    @classmethod
    def bulk_register(cls, accounts: list = [], commit: bool = True, remove: bool = False):
        for u in accounts:
            cls.add_or_update(commit=False, **u)
        if remove:
            dd = {str(u['uuid']): 1 for u in accounts}
            for d in cls.query.all():
                if d.uuid not in dd:
                    db.session.delete(d)  # type: ignore
        if commit:
            db.session.commit()  # type: ignore
