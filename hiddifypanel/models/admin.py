import uuid as uuid_mod
from enum import auto

from flask import g
from hiddifypanel import hutils
from hiddifypanel.models.usage import DailyUsage
from sqlalchemy_serializer import SerializerMixin
from strenum import StrEnum

from hiddifypanel.panel.database import db

from wtforms.validators import Regexp, ValidationError
from apiflask import abort
from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _


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


class AdminUser(db.Model, SerializerMixin):
    """
    This is a model class for a user in a database that includes columns for their ID, UUID, name, online status,
    account expiration date, usage limit, package days, mode, start date, current usage, last reset time, and comment.
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), default=lambda: str(uuid_mod.uuid4()), nullable=False, unique=True)
    name = db.Column(db.String(512), nullable=False)
    username = db.Column(db.String(16), nullable=True, default='')
    password = db.Column(db.String(16), nullable=True, default='')
    mode = db.Column(db.Enum(AdminMode), default=AdminMode.agent, nullable=False)
    can_add_admin = db.Column(db.Boolean, default=False, nullable=False)
    max_users = db.Column(db.Integer, default=100, nullable=False)
    max_active_users = db.Column(db.Integer, default=100, nullable=False)
    comment = db.Column(db.String(512))
    telegram_id = db.Column(db.String(512))
    users = db.relationship('User', backref='admin')
    usages = db.relationship('DailyUsage', backref='admin')
    parent_admin_id = db.Column(db.Integer, db.ForeignKey('admin_user.id'), default=1)
    parent_admin = db.relationship('AdminUser', remote_side=[id], backref='sub_admins')

    def recursive_users_query(self):
        from .user import User
        admin_ids = self.recursive_sub_admins_ids()
        return User.query.filter(User.added_by.in_(admin_ids))

    def can_have_more_users(admin):
        if admin.mode == AdminMode.super_admin:
            return True
        users_count = admin.recursive_users_query().count()
        if admin.max_users < users_count:
            return False
        if users_count <= admin.max_active_users:
            return True

        actives = [u for u in admin.recursive_users_query().all() if u.is_active]
        return len(actives) <= admin.max_active_users

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

    def remove(model):
        if model.id == 1 or model.id == g.account.id:
            # raise ValidationError(_("Owner can not be deleted!"))
            abort(422, __("Owner can not be deleted!"))
        users = model.recursive_users_query().all()
        for u in users:
            u.added_by = g.account.id

        DailyUsage.query.filter(DailyUsage.admin_id.in_(model.recursive_sub_admins_ids())).update({'admin_id': g.account.id})
        AdminUser.query.filter(AdminUser.id.in_(model.recursive_sub_admins_ids())).delete()

        db.session.commit()

    def __str__(self):
        return str(self.name)

    def to_dict(admin):
        return {
            'name': admin.name,
            'comment': admin.comment,
            'uuid': admin.uuid,
            'mode': admin.mode,
            'can_add_admin': admin.can_add_admin,
            'parent_admin_uuid': admin.parent_admin.uuid if admin.parent_admin else None,
            'telegram_id': admin.telegram_id
        }


def get_super_admin_secret():
    return get_super_admin().uuid


def get_super_admin():
    admin = AdminUser.query.filter(AdminUser.mode == AdminMode.super_admin).first()
    if not admin:
        db.session.add(AdminUser(mode=AdminMode.super_admin, name="Owner"))
        db.session.commit()
        admin = AdminUser.query.filter(AdminUser.mode == AdminMode.super_admin).first()

    return admin


def get_admin_user_db(uuid):
    return AdminUser.query.filter(AdminUser.uuid == uuid).first()


def add_or_update_admin(commit=True, **admin):
    # if not is_valid():return
    dbuser = AdminUser.query.filter(AdminUser.uuid == admin['uuid']).first()

    if not dbuser:
        dbuser = AdminUser(uuid=admin['uuid'])
        # if not is_valid():
        #     return
        db.session.add(dbuser)
    dbuser.name = admin['name']
    if dbuser.id != 1:
        parent = admin.get('parent_admin_uuid')
        if parent == admin['uuid'] or not parent:
            parent_admin = current_admin_or_owner()
        else:
            parent_admin = get_admin_by_uuid(parent, create=True)
        dbuser.parent_admin_id = parent_admin.id

    dbuser.comment = admin.get('comment', '')
    dbuser.mode = admin.get('mode', AdminMode.agent)
    dbuser.telegram_id = admin.get('telegram_id')
    dbuser.can_add_admin = admin.get('can_add_admin') == True

    # dbuser.last_online=user.get('last_online','')
    if commit:
        db.session.commit()
    return dbuser


def get_admin_by_uuid(uuid, create=False) -> AdminUser | None:
    admin = AdminUser.query.filter(AdminUser.uuid == uuid).first()
    # print(admin)
    if create and not admin:

        # print(parent_id)
        # raise (parent_id)
        dbuser = AdminUser(uuid=uuid, name="unknown", parent_admin_id=current_admin_or_owner().id)
        db.session.add(dbuser)
        db.session.commit()
        admin = AdminUser.query.filter(AdminUser.uuid == uuid).first()
    return admin


def get_admin_by_username(username) -> AdminUser | None:
    return AdminUser.query.filter(AdminUser.username == username).first()


def bulk_register_admins(users=[], commit=True):
    for u in users:
        add_or_update_admin(commit=False, **u)
    if commit:
        db.session.commit()


def current_admin_or_owner():
    if g and hasattr(g, 'account') and g.account and isinstance(g.account, AdminUser):
        return g.account
    return AdminUser.query.filter(AdminUser.id == 1).first()


def fill_username(admin: AdminUser) -> None:
    minimum_username_length = 10
    if not admin.username or len(admin.username) < 10:
        base_username = ''
        rand_str = ''
        # if the username chats isn't only string.ascii_letters, it's invalid
        # because we can't set non ascii characters in the http header (https://stackoverflow.com/questions/7242316/what-encoding-should-i-use-for-http-basic-authentication)
        if admin.name:
            # user actual name
            base_username = admin.name.replace(' ', '_')
            if len(base_username) > minimum_username_length - 1:
                # check if the name is unique, if  it's not we add some random char to it
                while AdminUser.query.filter(AdminUser.username == base_username + rand_str).first():
                    rand_str = hutils.utils.get_random_string(2, 4)
            else:
                needed_length = minimum_username_length - len(base_username)
                rand_str = hutils.utils.get_random_string(needed_length, needed_length)
                while AdminUser.query.filter(AdminUser.username == base_username + rand_str).first():
                    rand_str = hutils.utils.get_random_string(needed_length, needed_length)
        else:
            base_username = hutils.utils.get_random_string(minimum_username_length, minimum_username_length)
            while AdminUser.query.filter(AdminUser.username == base_username + rand_str).first():
                rand_str = hutils.utils.get_random_string(minimum_username_length, minimum_username_length)

        admin.username = base_username + rand_str if rand_str else base_username


def fill_password(admin: AdminUser) -> None:
    # TODO: hash the password
    if not admin.password or len(admin.password) < 16:
        base_passwd = hutils.utils.get_random_password()
        rand_str = ''
        # if passwd is duplicated, we create another one
        while AdminUser.query.filter(AdminUser.password == base_passwd + rand_str).first():
            rand_str = hutils.utils.get_random_password()
        admin.password = base_passwd + rand_str
