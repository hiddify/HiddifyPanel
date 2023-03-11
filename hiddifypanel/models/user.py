import datetime
import uuid as uuid_mod

from sqlalchemy_serializer import SerializerMixin
from dateutil import relativedelta
from hiddifypanel.panel.database import db
from enum import auto
from strenum import StrEnum


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
    disable = auto()


class User(db.Model, SerializerMixin):
    """
    This is a model class for a user in a database that includes columns for their ID, UUID, name, online status,
    account expiration date, usage limit, package days, mode, start date, current usage, last reset time, and comment.
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), default=lambda: str(uuid_mod.uuid4()), nullable=False, unique=True)
    name = db.Column(db.String(512), nullable=False)
    last_online = db.Column(db.DateTime, nullable=False, default=datetime.datetime.min)
    expiry_time = db.Column(db.Date, default=datetime.date.today() + relativedelta.relativedelta(months=6))
    usage_limit_GB = db.Column(db.Numeric(6, 9, asdecimal=False), default=1000, nullable=False)
    package_days = db.Column(db.Integer, default=90)
    mode = db.Column(db.Enum(UserMode), default=UserMode.no_reset)
    monthly = db.Column(db.Boolean, default=False)
    start_date = db.Column(db.Date, nullable=True)
    current_usage_GB = db.Column(db.Numeric(6, 9, asdecimal=False), default=0, nullable=False)
    last_reset_time = db.Column(db.Date, default=datetime.date.today())
    comment = db.Column(db.String(512))


def is_user_active(u):
    """
    The "is_user_active" function checks if the input user object "u" is active by verifying if their mode is not
    "disable", if their usage limit hasn't been exceeded, and if there are remaining days on their account. The
    function returns a boolean value indicating whether the user is active or not.
    """
    if u.mode == UserMode.disable:
        return False
    if u.usage_limit_GB < u.current_usage_GB:
        return False
    if remaining_days(u) < 0:
        return False
    return True


def remaining_days(u):
    """
    The "remaining_days" function calculates the number of days remaining for a user's account package based on the
    current date and the user's start date. The function returns the remaining days as an integer value. If the start
    date is not available, the function returns the total package days.
    """
    if not u.package_days:
        return -1
    if u.start_date:
        return u.package_days - (datetime.date.today() - u.start_date).days
    return u.package_days 


package_mode_dic = {
    UserMode.daily: 1,
    UserMode.weekly: 7,
    UserMode.monthly: 30
}


def days_to_reset(user):
    """
    The "days_to_reset" function calculates the number of days until the user's data usage is reset, based on the
    user's start date and mode of usage. The function returns the remaining days as an integer value. If the start
    date is not available, the function returns the total days for the user's mode.
    """
    if user.start_date:
        days=package_mode_dic.get(user.mode,10000)-(datetime.date.today()-user.start_date).days % package_mode_dic.get(user.mode,10000)
    else:
        days= package_mode_dic.get(user.mode,10000)
    return max(-100000,min(days,100000))



def user_by_uuid(uuid):
    return User.query.filter(User.uuid==uuid).first()

def user_by_id(id):
    return User.query.filter(User.id==id).first()
