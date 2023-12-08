import socket
from uuid import UUID
import user_agents
from sqlalchemy.orm import Load
import glob
import json
from babel.dates import format_timedelta as babel_format_timedelta
from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _
import datetime
from flask import jsonify, g, url_for, Markup, abort, current_app, request
from flask import flash as flask_flash
import re
from wtforms.validators import ValidationError
import requests

import string
import random
from babel.dates import format_timedelta as babel_format_timedelta
import urllib
import time
import os
import psutil
from urllib.parse import urlparse
import ssl
import h2.connection
import subprocess
import netifaces
import time
import sys

from hiddifypanel.cache import cache
to_gig_d = 1000*1000*1000


def url_encode(strr):
    import urllib.parse
    return urllib.parse.quote(strr)

def is_uuid_valid(uuid,version):
    try:
        uuid_obj = UUID(uuid, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid

def error(str):

    print(str, file=sys.stderr)


def static_url_for(**values):
    orig = url_for("static", **values)
    return orig.split("user_secret")[0]

@cache.cache(ttl=60000)
def get_latest_release_url(repo):
            latest_url = requests.get(f'{repo}/releases/latest').url.strip()
            version = latest_url.split('tag/')[1].strip()
            return (latest_url,version)
@cache.cache(ttl=600)
def get_latest_release_version(repo_name):
    try:
        url = f"https://github.com/hiddify/{repo_name}/releases/latest"
        response = requests.head(url, allow_redirects=False)

        location_header = response.headers.get("Location")
        if location_header:
            version = re.search(r"/([^/]+)/?$", location_header)
            if version:
                return version.group(1).replace('v', '')
    except Exception as e:
        return f'{e}'

    return None


def do_base_64(str):
    import base64
    resp = base64.b64encode(f'{str}'.encode("utf-8"))
    return resp.decode()


def get_folder_size(folder_path):
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for file in filenames:
                file_path = os.path.join(dirpath, file)
                try:
                    total_size += os.path.getsize(file_path)
                except:
                    pass
    except:
        pass
    return total_size


def get_random_string(min_=10, max_=30):
    # With combination of lower and upper case
    length = random.randint(min_, max_)
    characters = string.ascii_letters + string.digits
    result_str = ''.join(random.choice(characters) for i in range(length))
    return result_str


def date_to_json(d):
    return d.strftime("%Y-%m-%d") if d else None


def json_to_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return date_str


def time_to_json(d):

    return d.strftime("%Y-%m-%d %H:%M:%S") if d else None


def json_to_time(time_str):
    try:
        return datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except:
        return time_str
def fix_time_format(time_str):
    'Convert "1-00-00 00:00:00" to "0001-00-00 00:00:00"'
    t = time_str
    char_index = t.find('-')
    if len(t[:char_index]) != 4:
        if len(t[:char_index]) == 3:
            t = '0' + t
        elif len(t[:char_index]) == 2:
            t = '00' + t
        elif len(t[:char_index]) == 1:
            t = '000' + t
    return t

def mix_str_configs_and_bool_configs(data:dict):
    # mix str_configs and bool_configs to in a list
        data['hconfigs'] = []
        for s_c in data.get('str_configs',None):
            data['hconfigs'].append(s_c)
        for b_c in data.get('bool_configs',None):
            data['hconfigs'].append(b_c)


def flash(message, category):
    print(message)
    return flask_flash(Markup(message), category)
