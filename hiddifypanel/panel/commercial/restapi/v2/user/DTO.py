from apiflask import Schema
from apiflask.fields import Integer, String, Float, URL, Enum,List,Dict,Nested,Time
from apiflask.validators import Length, OneOf
from strenum import StrEnum
from enum import auto
from enum import Enum as StdEnum
from hiddifypanel.models import Lang


class ProfileSchema(Schema):
    profile_title = String(required=True)
    profile_url = URL(required=True)
    profile_usage_current = Float(required=True)
    profile_usage_total = Float(required=True)
    profile_remaining_days = Integer(required=True)
    profile_reset_days = Integer()
    telegram_bot_url = String()
    telegram_id = Integer()
    admin_message_html = String()
    admin_message_url = URL()
    brand_title = String()
    brand_icon_url = URL()
    doh = URL()
    lang = Enum(Lang,required=True)

class ConfigSchema(Schema):
    name = String(required=True)
    domain = String(required=True)
    link = String(required=True)
    protocol = String(required=True)
    transport = String(required=True)
    security = String(required=True)
    type = String(required=True)

class MtproxySchema(Schema):
    link = String(required=True)
    title = String(required=True)


class ShortSchema(Schema):
    short = String(required=True)
    full_url = String(required=True)
    expire_in = Integer(required=True)

class UserInfoChangableSchema(Schema):
    language = Enum(Lang,required=False)
    telegram_id = Integer(required=False)


#region App Api DTOs
class AppInstallType(StdEnum):
    GOOGLE_PLAY = auto()
    APP_STORE = auto()
    APPIMAGE = auto()
    SNAPCRAFT = auto()
    MICROSOFT_STORE = auto()
    APK = auto()
    DMG = auto()
    SETUP = auto()
    PORTABLE = auto()
    OTHER = auto()

class AppInstall(Schema):
    title = String()
    type = Enum(AppInstallType)
    url = URL()
# class DeeplinkType(Enum):
#     general = auto()
#     all_sites = auto()
#     blocked_sites = auto()
#     foreign_sites = auto()
class AppSchema(Schema):
    title = String(required=True)
    description = String()
    icon_url = URL()
    guide_url = URL()
    deeplink = URL()
    install = List(Nested(AppInstall()))

# this class is not a Data Transfer Object, It's just an enum
class Platform(StdEnum):
    android = auto()
    ios = auto()
    windows = auto()
    linux = auto()
    mac = auto()
#endregion