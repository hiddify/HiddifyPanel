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
ipasn = maxminddb.open_database('GeoLite2-ASN.mmdb') if os.path.exists('GeoLite2-ASN.mmdb') else None


asn_map={
    'AS58224':'ITC',
    'AS197207':'MCI',
    'AS12880':'ITC',
    'AS44244':'MTN',
    'AS31549':'RTL',
    'AS16322':'PRS',
    'AS56402':'HWB',
    'AS41689':'AST',
    'AS31549':'SHT',
    'AS50810':'MBT',
    'AS39308':'ASK',
    'AS205207':'RSP',
    'AS25184':'AFR',
    'AS394510':'ZTL',
    'AS49100':'PSM'
}
def get_real_user_ip():
    for header in ['CF-Connecting-IP','ar-real-ip']:
        if header in request.headers:
            return request.headers.get(header)
        
    return request.remote_addr
def get_clean_ip(ips):
    if not ips:
        ips=default_ips
        
    ips=re.split('[ \t\r\n;,]+',ips.strip())
    is_morteza_format=any([format for format in asn_map.values() if format in ips])
    print(ips)
    if is_morteza_format:
        try:
            user_ip=get_real_user_ip()
            asnres = ipasn.get(user_ip) if ipasn else {'autonomous_system_number':'unknown'}
            asn = asnres['autonomous_system_number']
            
            for i in range(0,len(ips),2):
                if asn_map.get(asn,ips[1])== ips[i+1]:
                    print("selected ",ips[i],ips[i+1])
                    return hiddify.get_domain_ip(ips[i])
        except Exception as e:
            print(e)
            flash(_("Error in morteza ip! auto cdn ip can not be find, please contact admin."))
    try:
        selected_server=random.sample(ips, 1)
        print("selected ",selected_server)
        return hiddify.get_domain_ip(selected_server[0])
    except Exception as e:
        print(e)
        flash(_("Error! auto cdn ip can not be find, please contact admin."))
