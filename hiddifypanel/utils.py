import socket
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
to_gig_d = 1000*1000*1000


def url_encode(strr):
    import urllib.parse
    return urllib.parse.quote(strr)


def error(str):

    print(str, file=sys.stderr)


def static_url_for(**values):
    orig = url_for("static", **values)
    return orig.split("user_secret")[0]


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
        return None


def time_to_json(d):
    return d.strftime("%Y-%m-%d %H:%M:%S") if d else None


def json_to_time(time_str):
    try:
        return datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except:
        return None


def flash(message, category):
    print(message)
    return flask_flash(Markup(message), category)


def get_domain_ip(dom, retry=3, version=None):

    res = None
    if not version:
        try:
            res = socket.gethostbyname(dom)
        except:
            pass

    if not res and version != 6:
        try:
            res = socket.getaddrinfo(dom, None, socket.AF_INET)[0][4][0]
        except:
            pass

    if not res and version != 4:
        try:
            res = f"[{socket.getaddrinfo(dom, None, socket.AF_INET6)[0][4][0]}]"
        except:
            pass

    if retry <= 0:
        return None

    return res or get_domain_ip(dom, retry=retry-1)


def get_socket_public_ip(version):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if version == 6:
            s.connect(("2001:4860:4860::8888", 80))
        else:
            s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()

        return ip_address if is_public_ip(ip_address) else None
    except socket.error:
        return None


def is_public_ip(address):
    if address.startswith('127.') or address.startswith('169.254.') or address.startswith('10.') or address.startswith('192.168.') or address.startswith('172.'):
        return False
    if address.startswith('fe80:') or address.startswith('fd') or address.startswith('fc00:'):
        return False
    if address.startswith('::') or address.startswith('fd') or address.startswith('fc00:'):
        return False
    return True


def get_interface_public_ip(version):
    addresses = []
    try:
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            if version == 4:
                address_info = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
            elif version == 6:
                address_info = netifaces.ifaddresses(interface).get(netifaces.AF_INET6, [])
            else:
                return None

            if address_info:
                for addr in address_info:
                    address = addr['addr']
                    if (is_public_ip(address)):
                        addresses.append(address)

        return addresses if addresses else None

    except (OSError, KeyError):
        return None
