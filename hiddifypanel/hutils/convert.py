from babel.dates import format_timedelta as babel_format_timedelta
from datetime import datetime
from datetime import timedelta
from flask import g

from hiddifypanel.models.config import hconfig
from hiddifypanel.models.config_enum import ConfigEnum
from flask_babel import gettext as _


def is_int(input: str) -> bool:
    try:
        int(input)
        return True
    except BaseException:
        return False


def to_int(s: str | None) -> int | None:
    '''Returns 0 if <s> is not a number'''
    if not s:
        return None
    try:
        return int(s)
    except BaseException:
        return 0


def date_to_json(d: datetime) -> str | None:
    return d.strftime("%Y-%m-%d") if d else None


def json_to_date(date_str: str) -> datetime | str:
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except BaseException:
        return date_str


def time_to_json(d: datetime) -> str | None:
    return __fix_time_format(d.strftime("%Y-%m-%d %H:%M:%S")) if d else None


def __fix_time_format(time_str):
    'Convert "1-00-00 00:00:00" to "0001-00-00 00:00:00"'
    t = time_str
    char_index = t.find('-')
    year_part = t[:char_index]

    if len(year_part) < 4:
        t = year_part.zfill(4) + t[char_index:]

    return t


def json_to_time(time_str: str) -> datetime | str:
    try:
        return datetime.strptime(__fix_time_format(time_str), "%Y-%m-%d %H:%M:%S")
    except BaseException:
        return json_to_date(time_str)


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
