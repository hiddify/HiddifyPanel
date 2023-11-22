from apiflask import Schema
from apiflask.fields import Integer, String, Float, URL, Enum, List, Dict, Nested, Time
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
    lang = Enum(Lang, required=True)


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
    short = String(required=True, description="the short url slug")
    full_url = String(required=True, description="full short url")
    expire_in = Integer(required=True, description="expire_in is in seconds")


class UserInfoChangableSchema(Schema):
    language = Enum(Lang, required=False)
    telegram_id = Integer(required=False)
