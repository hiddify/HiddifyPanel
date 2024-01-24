import base64
from typing import Any, Tuple
from urllib.parse import urlparse
from uuid import UUID
from flask_babelex import lazy_gettext as _
import re
import requests

import string
import os
import sys

from hiddifypanel.cache import cache


to_gig_d = 1000*1000*1000


def error(str):
    print(str, file=sys.stderr)


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


def is_assci_alphanumeric(str):
    for c in str:
        if c not in string.ascii_letters + string.digits:
            return False
    return True


def get_proxy_path_from_url(url: str) -> str | None:
    url_path = urlparse(url).path
    proxy_path = url_path.lstrip('/').split('/')[0] or None
    return proxy_path


def is_out_of_range_port(port: int) -> bool:
    return port < 1 or port > 65535
