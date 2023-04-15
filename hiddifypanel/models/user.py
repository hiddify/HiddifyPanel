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
    #removed
    expiry_time = db.Column(db.Date, default=datetime.date.today() + relativedelta.relativedelta(months=6))
    usage_limit_GB = db.Column(db.Numeric(6, 9, asdecimal=False), default=1000, nullable=False)
    package_days = db.Column(db.Integer, default=90,nullable=False)
    mode = db.Column(db.Enum(UserMode), default=UserMode.no_reset,nullable=False)
    monthly = db.Column(db.Boolean, default=False)#removed
    start_date = db.Column(db.Date, nullable=True)
    current_usage_GB = db.Column(db.Numeric(6, 9, asdecimal=False), default=0, nullable=False)
    last_reset_time = db.Column(db.Date, default=datetime.date.today())
    comment = db.Column(db.String(512))
    telegram_id=db.Column(db.String(512))
    added_by=db.Column(db.Integer,db.ForeignKey('admin_user.id'),default=0)
    
    @property
    def remaining_days(self):
        return remaining_days(self)
    @property
    def is_active(self):
        return is_user_active(self)

def is_user_active(u):
    """
    The "is_user_active" function checks if the input user object "u" is active by verifying if their mode is not
    "disable", if their usage limit hasn't been exceeded, and if there are remaining days on their account. The
    function returns a boolean value indicating whether the user is active or not.
    """
    is_active=True
    if not u:
        is_active=False
    elif u.mode == UserMode.disable:
        is_active= False
    elif u.usage_limit_GB < u.current_usage_GB:
        is_active= False
    elif remaining_days(u) < 0:
        is_active= False
    return is_active


def remaining_days(u):
    """
    The "remaining_days" function calculates the number of days remaining for a user's account package based on the
    current date and the user's start date. The function returns the remaining days as an integer value. If the start
    date is not available, the function returns the total package days.
    """
    res=-1
    if u.package_days is None:
        res= -1
    elif u.start_date:
        # print(datetime.date.today(), u.start_date,u.package_days, u.package_days - (datetime.date.today() - u.start_date).days)
        res=u.package_days - (datetime.date.today() - u.start_date).days
    else:
        # print("else",u.package_days )
        res=u.package_days 
    return min(res,10000)


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
    # print("start_date",user.start_date, "pack",package_mode_dic.get(user.mode,10000), "total",(datetime.date.today()-user.start_date).days)
    # if user.mode==UserMode.daily:
    #     return 0
    if user.start_date:
        days=package_mode_dic.get(user.mode,10000)-(datetime.date.today()-user.start_date).days % package_mode_dic.get(user.mode,10000)
    else:
        days= package_mode_dic.get(user.mode,10000)
    return max(-100000,min(days,100000))


def user_should_reset(user):
    """
    The "days_to_reset" function calculates the number of days until the user's data usage is reset, based on the
    user's start date and mode of usage. The function returns the remaining days as an integer value. If the start
    date is not available, the function returns the total days for the user's mode.
    """
    # print("start_date",user.start_date, "pack",package_mode_dic.get(user.mode,10000), "total",(datetime.date.today()-user.start_date).days)
    # if user.mode==UserMode.daily:
    #     return 0
    res=True
    if not user.last_reset_time:
        res=True
    elif not user.start_date or (datetime.date.today()-user.last_reset_time).days==0:
        res=False
    else:
        res=((datetime.date.today()-user.start_date).days % package_mode_dic.get(user.mode,10000))==0
    
    return res


def user_by_uuid(uuid):
    return User.query.filter(User.uuid==uuid).first()

def user_by_id(id):
    return User.query.filter(User.id==id).first()



def add_or_update_user(commit=True,**user):
    # if not is_valid():return
    dbuser = User.query.filter(User.uuid == user['uuid']).first()

    if not dbuser:
        dbuser = User()
        dbuser.uuid = user['uuid']
        # if not is_valid():
        #     return
        db.session.add(dbuser)
    
    if user.get('expiry_time',''):
        if user.get('last_reset_time',''):
            last_reset_time = datetime.datetime.strptime(user['last_reset_time'], '%Y-%m-%d')
        else:
            last_reset_time = datetime.date.today()

        expiry_time = datetime.datetime.strptime(user['expiry_time'], '%Y-%m-%d')
        dbuser.start_date=    last_reset_time
        dbuser.package_days=(expiry_time-last_reset_time).days

    elif 'package_days' in user:
        dbuser.package_days=user['package_days']
        if user.get('start_date',''):
            dbuser.start_date=datetime.datetime.strptime(user['start_date'], '%Y-%m-%d')
        else:
            dbuser.start_date=None
    dbuser.current_usage_GB = user['current_usage_GB']
    
    dbuser.usage_limit_GB = user['usage_limit_GB']
    dbuser.name = user['name']
    dbuser.comment = user.get('comment', '')
    dbuser.mode = user.get('mode', user.get('monthly', 'false') == 'true')
    # dbuser.last_online=user.get('last_online','')
    if commit:
        db.session.commit()
