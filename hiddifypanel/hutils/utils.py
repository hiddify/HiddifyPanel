from urllib.parse import urlparse
from uuid import UUID
from flask_babelex import lazy_gettext as _
from datetime import datetime
from flask import url_for, Markup
from flask import flash as flask_flash
import re
import requests

import string
import random
import os
import sys

from hiddifypanel.cache import cache
to_gig_d = 1000*1000*1000


def url_encode(strr):
    import urllib.parse
    return urllib.parse.quote(strr)


def is_uuid_valid(uuid, version):
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
    return (latest_url, version)


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


def get_random_password(length: int = 16) -> str:
    '''Retunrns a random password with fixed length'''
    characters = string.ascii_letters + string.digits  # + '-'
    while True:
        passwd = ''.join(random.choice(characters) for i in range(length))
        if (any(c.islower() for c in passwd) and any(c.isupper() for c in passwd) and sum(c.isdigit() for c in passwd) > 1):
            return passwd


def is_assci_alphanumeric(str):
    for c in str:
        if c not in string.ascii_letters + string.digits:
            return False
    return True


def date_to_json(d):
    return d.strftime("%Y-%m-%d") if d else None


def json_to_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return date_str


def time_to_json(d):

    return d.strftime("%Y-%m-%d %H:%M:%S") if d else None


def json_to_time(time_str):
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except:
        return time_str


def flash(message, category):
    print(message)
    return flask_flash(Markup(message), category)


def get_proxy_path_from_url(url: str) -> str | None:
    url_path = urlparse(url).path
    proxy_path = url_path.lstrip('/').split('/')[0] or None
    return proxy_path


def is_uuid_in_url_path(path: str) -> bool:
    for section in path.split('/'):
        if is_uuid_valid(section, 4):
            return True
    return False


def get_uuid_from_url_path(path: str) -> str | None:
    for section in path.split('/'):
        if is_uuid_valid(section, 4):
            return section
    return None
