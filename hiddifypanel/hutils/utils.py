import base64
from typing import Any, Tuple
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
    # print(message)
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


def get_uuid_from_url_path(path: str, section_index: int = 2) -> str | None:
    """
    Takes a URL path and extracts the UUID at the specified section index.

    Args:
        path (str): The URL path from which to extract the UUID.
        section_index (int, optional): The index of the section in the URL path where the UUID is located. Defaults to 2, because in past the UUID was in the second section of path of url.

    Returns:
        str | None: The extracted UUID as a string if found, or None if not found.
    """
    s_index = 1
    for section in path.lstrip('/').split('/'):
        if is_uuid_valid(section, 4):
            if s_index == section_index:
                return section
        s_index += 1
    return None


def get_apikey_from_auth_header(auth_header: str) -> str | None:
    if auth_header.startswith('ApiKey'):
        return auth_header.split('ApiKey ')[1].strip()
    return None


def get_basic_auth_from_auth_header(auth_header: str) -> str | None:
    if auth_header.startswith('Basic'):
        return auth_header.split('Basic ')[1].strip()
    return None


def parse_basic_auth_header(auth_header: str) -> tuple[str, str] | None:
    if not auth_header.startswith('Basic'):
        return None
    header_value = auth_header.split('Basic ')
    if len(header_value) < 2:
        return None
    username, password = map(lambda item: item.strip(), base64.urlsafe_b64decode(header_value[1].strip()).decode('utf-8').split(':'))
    return (username, password) if username and password else None


def parse_login_id(raw_id) -> Tuple[Any | None, str | None]:
    """
    Parses the given raw ID to extract the account type and ID.
    Args:
        raw_id (str): The raw ID to be parsed.
    Returns:
        Tuple[Any | None, str | None]: A tuple containing the account type and ID.
            The account type is either AccountType.admin or AccountType.user
            and the ID is a string. If the raw ID cannot be parsed, None is returned
            for both the account type and ID.
    """
    splitted = raw_id.split('_')
    if len(splitted) < 2:
        return None, None
    admin_or_user, id = splitted
    from hiddifypanel.models.role import AccountType
    account_type = AccountType.admin if admin_or_user == 'admin' else AccountType.user
    if not id or not account_type:
        return None, None
    return account_type, id


def add_basic_auth_to_url(url: str, username: str, password: str) -> str:
    if 'https://' in url:
        return url.replace('https://', f'https://{username}:{password}@')
    elif 'http://' in url:
        return url.replace('http://', f'http://{username}:{password}@')
    else:
        return url


def convert_to_int(s: str) -> int:
    try:
        return int(s)
    except:
        return 0
