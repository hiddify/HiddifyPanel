import datetime
import uuid as uuid_mod
from hiddifypanel import hutils
from hiddifypanel.models.role import Role
from sqlalchemy import Column, String
from sqlalchemy_serializer import SerializerMixin
from flask_login import UserMixin as FlaskLoginUserMixin

from hiddifypanel.panel.database import db


class BaseAccount(db.Model, SerializerMixin, FlaskLoginUserMixin):  # type: ignore
    __abstract__ = True
    uuid = Column(String(36), default=lambda: str(uuid_mod.uuid4()), nullable=False, unique=True)
    name = Column(String(512), nullable=False, default='')
    username = Column(String(100), nullable=True, default='')
    password = Column(String(100), nullable=True, default='')
    comment = Column(String(512), nullable=True, default='')
    telegram_id = Column(String(512), nullable=True, default='')

    @property
    def role(self) -> Role | None:
        from hiddifypanel.models.user import User
        from hiddifypanel.models.admin import AdminUser, AdminMode
        if isinstance(self, AdminUser):
            match self.mode:
                case AdminMode.super_admin:
                    return Role.super_admin
                case AdminMode.admin:
                    return Role.admin
                case AdminMode.agent:
                    return Role.agent
        if isinstance(self, User):
            return Role.user

    def get_id(self) -> str | None:
        """
        Get the ID of the account. (*only for flask_login)
        """
        from hiddifypanel.models.user import User
        from hiddifypanel.models.admin import AdminUser
        if isinstance(self, AdminUser):
            return f'admin_{self.id}'
        if isinstance(self, User):
            return f'user_{self.id}'

    def is_username_unique(self) -> bool:
        from hiddifypanel.models.user import User
        from hiddifypanel.models.admin import AdminUser

        model = None
        if isinstance(self, AdminUser):
            model = AdminUser.query.filter(AdminUser.username == self.username).first()
        else:
            model = User.query.filter(User.username == self.username).first()

        if model and model.id != self.id:
            return False
        return True

    def to_dict(self, convert_date=True) -> dict:
        from hiddifypanel.models.admin import AdminUser
        if isinstance(self, AdminUser):
            return {
                'name': self.name,
                'comment': self.comment,
                'uuid': self.uuid,
                'mode': self.mode,
                'can_add_admin': self.can_add_admin,
                'parent_admin_uuid': self.parent_admin.uuid if self.parent_admin else None,
                'telegram_id': hutils.utils.convert_to_int(self.telegram_id),
            }
        else:
            return {
                'uuid': self.uuid,
                'name': self.name,
                'last_online': hutils.utils.time_to_json(self.last_online) if convert_date else self.last_online,
                'usage_limit_GB': self.usage_limit_GB,
                'package_days': self.package_days,
                'mode': self.mode,
                'start_date': hutils.utils.date_to_json(self.start_date)if convert_date else self.start_date,
                'current_usage_GB': self.current_usage_GB,
                'last_reset_time': hutils.utils.date_to_json(self.last_reset_time) if convert_date else self.last_reset_time,
                'comment': self.comment,
                'added_by_uuid': self.admin.uuid,
                'telegram_id': hutils.utils.convert_to_int(self.telegram_id),
                'ed25519_private_key': self.ed25519_private_key,
                'ed25519_public_key': self.ed25519_public_key
            }

    @classmethod
    def by_id(cls, id: int):
        return cls.query.filter(cls.id == id).first()

    @classmethod
    def by_uuid(cls, uuid: str, create: bool = False):
        from hiddifypanel.models.user import User
        from hiddifypanel.models.admin import AdminUser
        account = None
        if cls.__subclasscheck__(User) or cls.__subclasscheck__(AdminUser):
            account = cls.query.filter(cls.uuid == uuid).first()

        if not account and create:
            if cls.__subclasscheck__(User):
                dbuser = User(uuid=uuid, name="unknown", added_by=AdminUser.current_admin_or_owner().id)
                db.session.add(dbuser)
                db.session.commit()
                account = cls.by_uuid(uuid)
            elif cls.__subclasscheck__(AdminUser):
                dbuser = AdminUser(uuid=uuid, name="unknown", parent_admin_id=cls.current_admin_or_owner().id)
                db.session.add(dbuser)
                db.session.commit()
                account = cls.by_uuid(uuid)  # AdminUser.query.filter(AdminUser.uuid == uuid).first()

        return account

    @classmethod
    def by_username_password(cls, username: str, password: str):
        return cls.query.filter(cls.username == username, cls.password == password).first()

    @classmethod
    def add_or_update(cls, commit: bool = True, **data):
        from hiddifypanel.models.user import User, UserMode
        from hiddifypanel.models.admin import AdminUser, AdminMode

        dbuser: AdminUser | User = None  # type: ignore
        if cls.__subclasscheck__(User):
            dbuser = User.by_uuid(data['uuid'], create=True)

            if data.get('added_by_uuid'):
                admin = AdminUser.by_uuid(data.get('added_by_uuid'), create=True)  # type: ignore
                dbuser.added_by = admin.id  # type: ignore
            else:
                dbuser.added_by = 1

            if data.get('expiry_time', ''):
                last_reset_time = hutils.utils.json_to_date(data.get('last_reset_time', '')) or datetime.date.today()

                expiry_time = hutils.utils.json_to_date(data['expiry_time'])
                dbuser.start_date = last_reset_time
                dbuser.package_days = (expiry_time-last_reset_time).days  # type: ignore

            elif 'package_days' in data:
                dbuser.package_days = data['package_days']
                if data.get('start_date', ''):
                    dbuser.start_date = hutils.utils.json_to_date(data['start_date'])
                else:
                    dbuser.start_date = None
            dbuser.current_usage_GB = data['current_usage_GB']

            dbuser.usage_limit_GB = data['usage_limit_GB']
            dbuser.name = data.get('name') or ''
            dbuser.comment = data.get('comment', '')
            dbuser.enable = data.get('enable', True)
            if data.get('ed25519_private_key', ''):
                dbuser.ed25519_private_key = data.get('ed25519_private_key', '')
                dbuser.ed25519_public_key = data.get('ed25519_public_key', '')
            if not dbuser.ed25519_private_key:
                from hiddifypanel.panel import hiddify
                priv, publ = hiddify.get_ed25519_private_public_pair()
                dbuser.ed25519_private_key = priv
                dbuser.ed25519_public_key = publ

            mode = data.get('mode', UserMode.no_reset)
            if mode == 'disable':
                mode = UserMode.no_reset
                dbuser.enable = False

            dbuser.mode = mode

            dbuser.telegram_id = data.get('telegram_id') or 0

            dbuser.last_online = hutils.utils.json_to_time(data.get('last_online')) or datetime.datetime.min
        elif cls.__subclasscheck__(AdminUser):
            # if not is_valid():return
            dbuser = cls.by_uuid(data['uuid'])  # type: ignore

            if not dbuser:
                dbuser = AdminUser(uuid=data['uuid'])
                # if not is_valid():
                #     return
                db.session.add(dbuser)
            dbuser.name = data['name']
            if dbuser.id != 1:
                parent = data.get('parent_admin_uuid')
                if parent == data['uuid'] or not parent:
                    parent_admin = cls.current_admin_or_owner()
                else:
                    parent_admin = cls.by_uuid(parent, create=True)
                dbuser.parent_admin_id = parent_admin.id  # type: ignore

            dbuser.comment = data.get('comment', '')
            dbuser.mode = data.get('mode', AdminMode.agent)
            dbuser.telegram_id = data.get('telegram_id')
            dbuser.can_add_admin = data.get('can_add_admin') == True

            # dbuser.last_online=user.get('last_online','')

        if commit:
            db.session.commit()
        return dbuser

    @classmethod
    def bulk_register(cls, accounts: list = [], commit: bool = True, remove: bool = False):
        from hiddifypanel.models.user import User
        from hiddifypanel.models.admin import AdminUser
        if cls.__subclasscheck__(User):
            for u in accounts:
                cls.add_or_update(commit=False, **u)
            if remove:
                dd = {u['uuid']: 1 for u in accounts}
                for d in cls.query.all():
                    if d.uuid not in dd:
                        db.session.delete(d)
        elif cls.__subclasscheck__(AdminUser):
            for u in accounts:
                cls.add_or_update(commit=False, **u)
        if commit:
            db.session.commit()
