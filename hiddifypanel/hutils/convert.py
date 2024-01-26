from babel.dates import format_timedelta as babel_format_timedelta
from datetime import datetime
from datetime import timedelta
from flask import g

from hiddifypanel.models.config import hconfig
from hiddifypanel.models.config_enum import ConfigEnum


def is_int(input: str) -> bool:
    try:
        int(input)
        return True
    except:
        return False


def to_int(s: str) -> int:
    '''Returns 0 if <s> is not a number'''
    try:
        return int(s)
    except:
        return 0


def date_to_json(d: datetime) -> str | None:
    return d.strftime("%Y-%m-%d") if d else None


def json_to_date(date_str: str) -> datetime | str:
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return date_str


def time_to_json(d: datetime) -> str | None:

    return d.strftime("%Y-%m-%d %H:%M:%S") if d else None


def json_to_time(time_str: str) -> datetime | str:
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except:
        return time_str


def format_timedelta(delta: timedelta, add_direction: bool = True, granularity: str = "days") -> str:
    res = delta.days
    locale = g.locale if g and hasattr(g, "locale") else hconfig(ConfigEnum.admin_lang)
    if granularity == "days" and delta.days == 0:
        res = _("0 - Last day")
    elif delta.days < 7 or delta.days >= 60:
        res = babel_format_timedelta(delta, threshold=1, add_direction=add_direction, locale=locale)
    elif delta.days < 60:
        res = babel_format_timedelta(delta, granularity="day", threshold=10, add_direction=add_direction, locale=locale)
    return str(res)
