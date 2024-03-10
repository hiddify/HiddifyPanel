from flask_babel import gettext as _
from typing import List, Union
from flask import request
import maxminddb
import random
import os
import re
import sys
from hiddifypanel.cache import cache
from hiddifypanel.models.config import hconfig
from hiddifypanel.models.config_enum import ConfigEnum
from hiddifypanel import hutils

DEFAULT_IPs = """
mci.ircf.space		MCI
mcix.ircf.space		MCI
mtn.ircf.space		MTN
mtnx.ircf.space		MTN
mkh.ircf.space		MKH
mkhx.ircf.space		MKH
rtl.ircf.space		RTL
hwb.ircf.space		HWB
ast.ircf.space		AST
sht.ircf.space		SHT
prs.ircf.space		PRS
mbt.ircf.space		MBT
ask.ircf.space		ASK
rsp.ircf.space		RSP
afn.ircf.space		AFN
ztl.ircf.space		ZTL
psm.ircf.space		PSM
arx.ircf.space		ARX
smt.ircf.space		SMT
fnv.ircf.space		FNV
dbn.ircf.space		DBN
apt.ircf.space		APT
"""

try:
    IPASN = maxminddb.open_database('GeoLite2-ASN.mmdb') if os.path.exists('GeoLite2-ASN.mmdb') else {}
    IPCOUNTRY = maxminddb.open_database('GeoLite2-Country.mmdb') if os.path.exists('GeoLite2-Country.mmdb') else {}
    __ipcity = maxminddb.open_database('GeoLite2-City.mmdb') if os.path.exists('GeoLite2-City.mmdb') else {}
except Exception as e:
    print("Error can not load maxminddb", file=sys.stderr)
    IPASN = {}
    IPCOUNTRY = {}

__asn_map = {
    '58224': 'MKH',
    '197207': 'MCI',
    '12880': 'ITC',
    '44244': 'MTN',
    '57218': 'RTL',
    '16322': 'PRS',
    '56402': 'HWB',
    '41689': 'AST',
    '43754': 'AST',
    '31549': 'SHT',
    '205647': 'SHT',
    '50810': 'MBT',
    '39308': 'ASK',
    '205207': 'RSP',
    '25184': 'AFR',
    '394510': 'ZTL',
    '206065': 'ZTL',
    '49100': 'PSM'
}


def get_asn_short_name(user_ip: str = '') -> str:
    return __get_asn_short_name_imp(user_ip or get_real_user_ip())


@cache.cache()
def __get_asn_short_name_imp(user_ip: str) -> str:
    try:
        asn_id = get_asn_id(user_ip)
        return __asn_map.get(str(asn_id), "unknown")
    except BaseException:
        return "unknown"


def get_asn_id(user_ip: str = '') -> str:
    return __get_asn_id_imp(user_ip or get_real_user_ip())


@cache.cache()
def __get_asn_id_imp(user_ip: str) -> str:
    try:
        asnres = IPASN.get(user_ip)
        return asnres['autonomous_system_number']
    except BaseException:
        return "unknown"


def get_country(user_ip: str = '') -> Union[dict, str]:
    try:
        user_ip = user_ip or get_real_user_ip()
        return (IPCOUNTRY.get(user_ip) or {}).get('country', {}).get('iso_code', 'unknown')
    except BaseException:
        return 'unknown'


def get_city(user_ip: str = '') -> Union[dict, str]:
    try:
        user_ip = user_ip or get_real_user_ip()
        res = __ipcity.get(user_ip)
        return {'city': res.get('city').get('name'), 'latitude': res.get('latitude'), 'longitude': res.get('longitude'), 'accuracy_radius': res.get('accuracy_radius')}
    except BaseException:
        return 'unknown'


def get_real_user_ip_debug(user_ip: str = '') -> str:
    return __get_real_user_ip_debug_imp(user_ip or get_real_user_ip())


@cache.cache()
def __get_real_user_ip_debug_imp(user_ip) -> str:
    if type(user_ip) is str and ',' in user_ip:
        user_ip = user_ip.split(',')[0]
    asnres = IPASN.get(user_ip) or {}
    asn = f"{asnres.get('autonomous_system_number','unknown')}" if asnres else "unknown"
    asn_dscr = f"{asnres.get('autonomous_system_organization','unknown')}" if asnres else "unknown"
    asn_short = get_asn_short_name(user_ip)
    country = get_country(user_ip)
    default = __get_host_base_on_asn(DEFAULT_IPs, asn_short).replace(".ircf.space", "")
    return f'{user_ip} {country} {asn} {asn_short} {"ERROR" if asn_short=="unknown" else ""} fullname={asn_dscr} default:{default}'


def get_real_user_ip() -> str:
    user_ip = request.remote_addr
    for header in ['CF-Connecting-IP', 'ar-real-ip', 'X-Forwarded-For', "X-Real-IP"]:
        if header in request.headers:
            user_ip = request.headers.get(header)
            break

    return str(user_ip)


def __get_host_base_on_asn(ips: Union[str, List[str]], asn_short: str) -> str:
    if type(ips) == str:
        ips = re.split('[ \t\r\n;,]+', ips.strip())
    valid_hosts = [ip for ip in ips if len(ip) > 5]

    if len(ips) % 2 != 0 or len(valid_hosts) == 0:
        hutils.flask.flash(_("Error! auto cdn ip can not be find, please contact admin."))
        if len(valid_hosts) == 0:
            return ''

    all_hosts = []
    for i in range(0, len(ips), 2):
        if asn_short == ips[i + 1]:
            # print("selected ",ips[i],ips[i+1])
            all_hosts.append(ips[i])

    selected = random.sample(valid_hosts, 1)[0]
    if len(all_hosts):
        selected = random.sample(all_hosts, 1)[0]

    return selected


def get_clean_ip(ips: Union[str, List[str]], resolve: bool = False, default_asn: str = '') -> str:
    if not ips:
        ips = DEFAULT_IPs

    ips = re.split('[ \t\r\n;,]+', ips.strip())
    user_ip = get_real_user_ip()
    asn_short = get_asn_short_name(user_ip)
    country = get_country(user_ip)
    # print("Real user ip",get_real_user_ip_debug(), user_ip,asn_short,country)
    is_morteza_format = any([format for format in __asn_map.values() if format in ips])
    # print("IPs",ips)
    if is_morteza_format:
        if str(country).lower() != hconfig(ConfigEnum.country) and default_asn:
            asn_short = default_asn
        selected_server = __get_host_base_on_asn(ips, asn_short)
    else:
        selected_server = random.sample(ips, 1)[0]
    # print("selected_server",selected_server)
    if resolve:
        selected_server = hutils.network.get_domain_ip(selected_server) or selected_server
    return str(selected_server)
