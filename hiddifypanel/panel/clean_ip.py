from flask_babelex import gettext as _
default_ips="""
mcix.ircf.space		MCI
mci.ircf.space		MCI
mtn.ircf.space		MTN
mtnx.ircf.space		MTN
rtl.ircf.space		RTL
mkh.ircf.space		MKH
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
"""
from flask import request,flash
import maxminddb
import os
import re
import random
from hiddifypanel.panel import hiddify
ipasn = maxminddb.open_database('GeoLite2-ASN.mmdb') if os.path.exists('GeoLite2-ASN.mmdb') else {}
ipcountry = maxminddb.open_database('GeoLite2-Country.mmdb') if os.path.exists('GeoLite2-Country.mmdb') else {}


asn_map={
    '58224':'ITC',
    '197207':'MCI',
    '12880':'ITC',
    '44244':'MTN',
    '57218':'RTL',
    '16322':'PRS',
    '56402':'HWB',
    '41689':'AST',
    '31549':'SHT',
    '50810':'MBT',
    '39308':'ASK',
    '205207':'RSP',
    '25184':'AFR',
    '394510':'ZTL',
    '206065':'ZTL',
    '49100':'PSM'
}

def get_asn_short_name(user_ip=None):
    user_ip=user_ip or get_real_user_ip()
    asnres = ipasn.get(user_ip) if ipasn else {'autonomous_system_number':'unknown'}
    asn = f"{asnres.get('autonomous_system_number','unknown')}" if asnres else "unknown"
    return asn_map.get(asn,"unknown") 
def get_country(user_ip=None):
    user_ip=user_ip or get_real_user_ip()
    return (ipcountry.get(user_ip) or {}).get('country',{}).get('iso_code','unknown')
def get_real_user_ip_debug(user_ip=None):
    user_ip=user_ip or get_real_user_ip()
    asnres = ipasn.get(user_ip) or {}
    asn = f"{asnres.get('autonomous_system_number','unknown')}" if asnres else "unknown"
    asn_dscr = f"{asnres.get('autonomous_system_organization','unknown')}" if asnres else "unknown"
    asn_short=get_asn_short_name(user_ip)
    country=get_country(user_ip)
    return f'{user_ip} {country} {asn} {asn_short} {"ERROR" if asn_short=="unknown" else ""} fullname={asn_dscr}' 

def get_real_user_ip():
    for header in ['CF-Connecting-IP','ar-real-ip']:
        if header in request.headers:
            return request.headers.get(header)
        
    return request.remote_addr
def get_clean_ip(ips,resolve=False,default_asn=None):
    if not ips:
        ips=default_ips
        
    ips=re.split('[ \t\r\n;,]+',ips.strip())
    is_morteza_format=any([format for format in asn_map.values() if format in ips])
    print(ips)
    if is_morteza_format:
        try:
            user_ip=get_real_user_ip()
            asn_short = get_asn_short_name(user_ip)
            country=get_country(user_ip)
            if country!="IR" and default_asn:
                asn_short=default_asn

            for i in range(0,len(ips),2):
                if asn_short == ips[i+1]:
                    print("selected ",ips[i],ips[i+1])
                    if resolve:
                        return hiddify.get_domain_ip(ips[i])
                    return ips[i]
        except Exception as e:
            print(e)
            flash(_("Error in morteza ip! auto cdn ip can not be find, please contact admin."))
    try:
        selected_server=random.sample(ips, 1)
        print("selected ",selected_server)
        if resolve:
            return hiddify.get_domain_ip(selected_server[0])
        return selected_server[0]
    except Exception as e:
        print(e)
        flash(_("Error! auto cdn ip can not be find, please contact admin."))
