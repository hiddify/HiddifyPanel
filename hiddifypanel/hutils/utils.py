from flask_babel import lazy_gettext as _
import requests
from packaging.version import Version
import re
import sys

from hiddifypanel.models.config import hconfig, ConfigEnum
from hiddifypanel import __version__ as current_version
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
    except Exception:
        return None

    return None


def is_panel_outdated() -> bool:
    # TODO: handle beta and develop version too
    pm = hconfig(ConfigEnum.package_mode)
    try:
        if pm == 'release':
            if latest_v := get_latest_release_version('hiddifypanel'):
                if compare_versions(latest_v, current_version) == 1:
                    return True
    except:
        pass
    return False


def compare_versions(version_1: str, version_2: str) -> int:
    """
    Compare two version strings and return an integer based on their relative order.
    Returns:
        int:

        - 1 if version_1 is greater than version_2.
        - 0 if version_1 is equal to version_2.
        - -1 if version_1 is less than version_2.

    Examples:
        >>> compare_versions("10.20.4", "10.20.4")
        0
        >>> compare_versions("10.20.4", "10.20.2")
        1
        >>> compare_versions("10.20.2", "10.20.4")
        -1
    """
    v1 = Version(version_1)
    v2 = Version(version_2)

    if v1 > v2:
        return 1  # version_1 is greater
    elif v2 > v1:
        return -1  # version_2 is greater
    else:
        return 0  # versions are equal
