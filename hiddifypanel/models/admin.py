from enum import auto
from flask import g
from hiddifypanel.models.usage import DailyUsage
from hiddifypanel.models.utils import fill_username, fill_password
from sqlalchemy import event
from strenum import StrEnum
from apiflask import abort
from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _

from hiddifypanel.panel.database import db
from .base_account import BaseAccount


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


class AdminUser(BaseAccount):
    """
    This is a model class for a user in a database that includes columns for their ID, UUID, name, online status,
    account expiration date, usage limit, package days, mode, start date, current usage, last reset time, and comment.
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mode = db.Column(db.Enum(AdminMode), default=AdminMode.agent, nullable=False)
    can_add_admin = db.Column(db.Boolean, default=False, nullable=False)
    max_users = db.Column(db.Integer, default=100, nullable=False)
    max_active_users = db.Column(db.Integer, default=100, nullable=False)
    users = db.relationship('User', backref='admin')
    usages = db.relationship('DailyUsage', backref='admin')
    parent_admin_id = db.Column(db.Integer, db.ForeignKey('admin_user.id'), default=1)
    parent_admin = db.relationship('AdminUser', remote_side=[id], backref='sub_admins')
    # These columns are created by BaseAccount
    # uuid = db.Column(db.String(36), default=lambda: str(uuid_mod.uuid4()), nullable=False, unique=True)
    # name = db.Column(db.String(512), nullable=False)
    # username = db.Column(db.String(16), nullable=True, default='')
    # password = db.Column(db.String(16), nullable=True, default='')
    # comment = db.Column(db.String(512))
    # telegram_id = db.Column(db.String(512))

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
                sub_admin_ids += sub_admin.recursive_sub_admins_ids(depth-1, seen=seen)
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
    def get_super_admin():
        admin = AdminUser.query.filter(AdminUser.mode == AdminMode.super_admin).first()
        if not admin:
            db.session.add(AdminUser(mode=AdminMode.super_admin, name="Owner"))
            db.session.commit()
            admin = AdminUser.query.filter(AdminUser.mode == AdminMode.super_admin).first()

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
    fill_username(target)
    fill_password(target)
