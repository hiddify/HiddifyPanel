import datetime
from enum import auto

from dateutil import relativedelta
from sqlalchemy_serializer import SerializerMixin
from strenum import StrEnum
from sqlalchemy import event

from hiddifypanel.panel.database import db
from hiddifypanel.models import Lang
from hiddifypanel.models.utils import fill_password, fill_username
from .base_account import BaseAccount

ONE_GIG = 1024*1024*1024


class UserMode(StrEnum):
    """
    The "UserMode" class is an enumeration that defines five possible modes: "no_reset", "monthly", "weekly",
    "daily", and "disable". These modes represent different settings that can be applied to a user account,
    such as the frequency at which data is reset or whether the account is currently disabled. The class is
    implemented using the "StrEnum" base class and the "auto()" function to generate unique values for each mode.
    """
    no_reset = auto()
    monthly = auto()
    weekly = auto()
    daily = auto()

    # disable = auto()
package_mode_dic = {
    UserMode.daily: 1,
    UserMode.weekly: 7,
    UserMode.monthly: 30
}


class UserDetail(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), default=0, nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), default=0, nullable=False)
    last_online = db.Column(db.DateTime, nullable=False, default=datetime.datetime.min)
    current_usage = db.Column(db.BigInteger, default=0, nullable=False)
    connected_ips = db.Column(db.String(512), default='', nullable=False)

    @property
    def current_usage_GB(self):
        return (self.current_usage or 0)/ONE_GIG

    @current_usage_GB.setter
    def current_usage_GB(self, value):
        self.current_usage = (value or 0)*ONE_GIG

    @property
    def ips(self):
        return [] if not self.connected_ips else self.connected_ips.split(",")


class User(BaseAccount):
    """
    This is a model class for a user in a database that includes columns for their ID, UUID, name, online status,
    account expiration date, usage limit, package days, mode, start date, current usage, last reset time, and comment.
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    last_online = db.Column(db.DateTime, nullable=False, default=datetime.datetime.min)
    # removed
    expiry_time = db.Column(db.Date, default=datetime.date.today() + relativedelta.relativedelta(months=6))
    usage_limit = db.Column(db.BigInteger, default=1000*ONE_GIG, nullable=False)
    package_days = db.Column(db.Integer, default=90, nullable=False)
    mode = db.Column(db.Enum(UserMode), default=UserMode.no_reset, nullable=False)
    monthly = db.Column(db.Boolean, default=False)  # removed
    start_date = db.Column(db.Date, nullable=True)
    current_usage = db.Column(db.BigInteger, default=0, nullable=False)
    last_reset_time = db.Column(db.Date, default=datetime.date.today())
    added_by = db.Column(db.Integer, db.ForeignKey('admin_user.id'), default=1)
    max_ips = db.Column(db.Integer, default=1000, nullable=False)
    details = db.relationship('UserDetail', cascade="all,delete", backref='user',    lazy='dynamic',)
    enable = db.Column(db.Boolean, default=True, nullable=False)
    lang = db.Column(db.Enum(Lang), default=None)
    ed25519_private_key = db.Column(db.String(500))
    ed25519_public_key = db.Column(db.String(100))
    # These columns are created by BaseAccount
    # uuid = db.Column(db.String(36), default=lambda: str(uuid_mod.uuid4()), nullable=False, unique=True)
    # name = db.Column(db.String(512), nullable=False, default='')
    # username = db.Column(db.String(16), nullable=True, default='')
    # password = db.Column(db.String(16), nullable=True, default='')
    # comment = db.Column(db.String(512))
    # telegram_id = db.Column(db.String(512))

    @property
    def current_usage_GB(self):
        return (self.current_usage or 0)/ONE_GIG

    @current_usage_GB.setter
    def current_usage_GB(self, value):
        self.current_usage = min(1000000*ONE_GIG, (value or 0)*ONE_GIG)

    @property
    def usage_limit_GB(self):
        return (self.usage_limit or 0)/ONE_GIG

    @usage_limit_GB.setter
    def usage_limit_GB(self, value):
        self.usage_limit = min(1000000*ONE_GIG, (value or 0)*ONE_GIG)

    @property
    def is_active(self) -> bool:
        """
        The "is_active" function checks if the input user object "user" is active by verifying if their mode is not
        "disable", if their usage limit hasn't been exceeded, and if there are remaining days on their account. The
        function returns a boolean value indicating whether the user is active or not.
        """
        is_active = True
        if not self:
            is_active = False
        elif not self.enable:
            is_active = False
        elif self.usage_limit < self.current_usage:
            is_active = False
        elif self.remaining_days() < 0:
            is_active = False
        elif len(self.ips) > max(3, self.max_ips):
            is_active = False
        return is_active

    @property
    def ips(self):
        res = {}
        for detail in UserDetail.query.filter(UserDetail.user_id == self.id):
            for ip in detail.ips:
                res[ip] = 1
        return list(res.keys())

    def user_should_reset(self) -> bool:
        # print("start_date",user.start_date, "pack",package_mode_dic.get(user.mode,10000), "total",(datetime.date.today()-user.start_date).days)
        # if user.mode==UserMode.daily:
        #     return 0
        res = True
        if not self.last_reset_time:
            res = True
        elif not self.start_date or (datetime.date.today()-self.last_reset_time).days == 0:
            res = False
        else:
            res = ((datetime.date.today()-self.start_date).days % package_mode_dic.get(self.mode, 10000)) == 0

        return res

    def days_to_reset(self):
        """
        The "days_to_reset" function calculates the number of days until the user's data usage is reset, based on the
        user's start date and mode of usage. The function returns the remaining days as an integer value. If the start
        date is not available, the function returns the total days for the user's mode.
        """
        # print("start_date",user.start_date, "pack",package_mode_dic.get(user.mode,10000), "total",(datetime.date.today()-user.start_date).days)
        # if user.mode==UserMode.daily:
        #     return 0
        if self.start_date:
            days = package_mode_dic.get(self.mode, 10000)-(datetime.date.today()-self.start_date).days % package_mode_dic.get(self.mode, 10000)
        else:
            days = package_mode_dic.get(self.mode, 10000)
        return max(-100000, min(days, 100000))

    def remaining_days(self) -> int:
        """
        The "remaining_days" function calculates the number of days remaining for a user's account package based on the
        current date and the user's start date. The function returns the remaining days as an integer value. If the start
        date is not available, the function returns the total package days.
        """
        res = -1
        if self.package_days is None:
            res = -1
        elif self.start_date:
            # print(datetime.date.today(), u.start_date,u.package_days, u.package_days - (datetime.date.today() - u.start_date).days)
            res = self.package_days - (datetime.date.today() - self.start_date).days
        else:
            # print("else",u.package_days )
            res = self.package_days
        return min(res, 10000)

    @staticmethod
    def from_dict(data):
        """
        Returns a new User object created from a dictionary.
        """

        return User(
            name=data.get('name', ''),
            expiry_time=data.get('expiry_time', datetime.date.today() + relativedelta.relativedelta(months=6)),
            usage_limit_GB=data.get('usage_limit_GB', 1000),
            package_days=data.get('package_days', 90),
            mode=UserMode[data.get('mode', 'no_reset')],
            monthly=data.get('monthly', False),
            start_date=data.get('start_date', None),
            current_usage_GB=data.get('current_usage_GB', 0),
            last_reset_time=data.get('last_reset_time', datetime.date.today()),
            comment=data.get('comment', None),
            telegram_id=data.get('telegram_id', None),
            added_by=data.get('added_by', 1)
        )


# TODO: refactor this function too
def remove(user: User, commit=True) -> None:
    from hiddifypanel.drivers import user_driver
    user_driver.remove_client(user)
    user.delete()
    if commit:
        db.session.commit()

# TODO: refactor this function too


def remove_user(uuid: str, commit=True):
    dbuser = User.by_uuid(uuid)
    db.session.delete(dbuser)
    if commit:
        db.session.commit()


@event.listens_for(User, 'before_insert')
def on_user_insert(mapper, connection, target):
    fill_username(target)
    fill_password(target)
