from enum import auto
from uuid import uuid4
from flask import g
from hiddifypanel.models.usage import DailyUsage
from sqlalchemy import event, Column, Integer, Enum, Boolean, ForeignKey
from strenum import StrEnum
from apiflask import abort
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from hiddifypanel.database import db, db_execute
from hiddifypanel.models.role import Role
from hiddifypanel.models.base_account import BaseAccount
from sqlalchemy_serializer import SerializerMixin


class AdminMode(StrEnum):
    """
    The "UserMode" class is an enumeration that defines five possible modes: "no_reset", "monthly", "weekly",
    "daily", and "disable". These modes represent different settings that can be applied to a user account,
    such as the frequency at which data is reset or whether the account is currently disabled. The class is
    implemented using the "StrEnum" base class and the "auto()" function to generate unique values for each mode.
    """
    super_admin = auto()
    admin = auto()
    agent = auto()


class AdminUser(BaseAccount, SerializerMixin):
    """
    This is a model class for a user in a database that includes columns for their ID, UUID, name, online status,
    account expiration date, usage limit, package days, mode, start date, current usage, last reset time, and comment.
    """
    id = Column(Integer, primary_key=True, autoincrement=True)
    mode = Column(Enum(AdminMode), default=AdminMode.agent, nullable=False)
    can_add_admin = Column(Boolean, default=False, nullable=False)
    max_users = Column(Integer, default=100, nullable=False)
    max_active_users = Column(Integer, default=100, nullable=False)
    users = db.relationship('User', backref='admin')  # type: ignore
    usages = db.relationship('DailyUsage', backref='admin')  # type: ignore
    parent_admin_id = Column(Integer, ForeignKey('admin_user.id'), default=1)
    parent_admin = db.relationship('AdminUser', remote_side=[id], backref='sub_admins')  # type: ignore

    @property
    def role(self) -> Role | None:
        match self.mode:
            case AdminMode.super_admin:
                return Role.super_admin
            case AdminMode.admin:
                return Role.admin
            case AdminMode.agent:
                return Role.agent
        return None

    @staticmethod
    def form_schema(schema):
        return schema.dump(AdminUser())

    def to_schema(self):
        admin_dict = self.to_dict()
        from hiddifypanel.panel.commercial.restapi.v2.admin.admin_user_api import AdminSchema
        return AdminSchema().load(admin_dict)

    def get_id(self) -> str | None:
        return f'admin_{self.id}'

    def to_dict(self, convert_date=True, dump_id=False) -> dict:
        base = super().to_dict()
        if dump_id:
            base['id'] = self.id
        if not base.get('lang'):
            from hiddifypanel.models import hconfig, ConfigEnum
            base['lang'] = hconfig(ConfigEnum.admin_lang)
        return {**base,
                'mode': self.mode,
                'can_add_admin': self.can_add_admin,
                'parent_admin_uuid': self.parent_admin.uuid if self.parent_admin else None,
                'max_users': self.max_users,
                'max_active_users': self.max_active_users,
                }

    @classmethod
    def by_uuid(cls, uuid: str, create: bool = False) -> BaseAccount | None:
        if not isinstance(uuid, str):
            uuid = str(uuid)
        account = AdminUser.query.filter(AdminUser.uuid == uuid).first()
        if not account and create:
            from hiddifypanel import hutils
            if not hutils.auth.is_uuid_valid(uuid):
                uuid = str(uuid4())
            dbuser = AdminUser(uuid=uuid, name="unknown", parent_admin_id=AdminUser.current_admin_or_owner().id)
            db.session.add(dbuser)
            db.session.commit()
            account = AdminUser.by_uuid(uuid, False)

        return account

    @classmethod
    def add_or_update(cls, commit: bool = True, **data):

        dbuser = super().add_or_update(commit=commit, **data)

        if dbuser.id != 1:
            parent = data.get('parent_admin_uuid')
            if parent == data['uuid'] or not parent:
                parent_admin = cls.current_admin_or_owner()
            else:
                parent_admin = cls.by_uuid(parent, create=True)
            dbuser.parent_admin_id = parent_admin.id  # type: ignore
        if data.get('mode') is not None:
            dbuser.mode = data.get('mode', AdminMode.agent)
        if data.get('can_add_admin') is not None:
            dbuser.can_add_admin = data['can_add_admin']
        if data.get('max_users') is not None:
            dbuser.max_users = data['max_users']
        if data.get('max_active_users') is not None:
            dbuser.max_active_users = data['max_active_users']
        if commit:
            db.session.commit()
        return dbuser

    def recursive_users_query(self):
        from .user import User
        admin_ids = self.recursive_sub_admins_ids()
        return User.query.filter(User.added_by.in_(admin_ids))

    def can_have_more_users(self):
        if self.mode == AdminMode.super_admin:
            return True
        users_count = self.recursive_users_query().count()
        if self.max_users < users_count:
            return False
        if users_count <= self.max_active_users:
            return True

        actives = [u for u in self.recursive_users_query().all() if u.is_active]
        return len(actives) <= self.max_active_users

    def recursive_sub_admins_ids(self, depth=20, seen=None):
        if seen is None:
            seen = set()
        sub_admin_ids = []
        if self.id not in seen:
            sub_admin_ids.append(self.id)
            seen.add(self.id)
        if depth > 0:
            for sub_admin in self.sub_admins:
                sub_admin_ids += sub_admin.recursive_sub_admins_ids(depth - 1, seen=seen)
        return sub_admin_ids

    def remove(self):
        if self.id == 1 or self.id == g.account.id:
            # raise ValidationError(_("Owner can not be deleted!"))
            abort(422, __("Owner can not be deleted!"))
        users = self.recursive_users_query().all()
        for u in users:
            u.added_by = g.account.id

        DailyUsage.query.filter(DailyUsage.admin_id.in_(self.recursive_sub_admins_ids())).update({'admin_id': g.account.id})
        AdminUser.query.filter(AdminUser.id.in_(self.recursive_sub_admins_ids())).delete()

        db.session.commit()

    def __str__(self):
        return str(self.name)

    @staticmethod
    def get_super_admin() -> "AdminUser":
        admin = AdminUser.by_id(1)
        if not admin:
            db.session.add(AdminUser(id=1, uuid=str(uuid4()), name="Owner", mode=AdminMode.super_admin, comment=""))
            db.session.commit()

            db_execute("update admin_user set id=1 where name='Owner'", commit=True)
            admin = AdminUser.by_id(1)

        return admin

    @staticmethod
    def get_super_admin_uuid() -> str:
        return AdminUser.get_super_admin().uuid

    @staticmethod
    def current_admin_or_owner():
        if g and hasattr(g, 'account') and g.account and isinstance(g.account, AdminUser):
            return g.account
        return AdminUser.query.filter(AdminUser.id == 1).first()


@event.listens_for(AdminUser, "before_insert")
def before_insert(mapper, connection, target):
    from hiddifypanel import hutils
    hutils.model.gen_username(target)
    hutils.model.gen_password(target)
