from flask_babel import lazy_gettext as _
import requests

import re
import sys

from hiddifypanel.cache import cache


to_gig_d = 1000 * 1000 * 1000


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
                ver = version.group(1).replace('v', '')
                if ver == "latest":
                    return get_latest_release_version(repo_name.replace("-", ""))
                return ver
    except Exception as e:
        return f'{e}'

    return None
