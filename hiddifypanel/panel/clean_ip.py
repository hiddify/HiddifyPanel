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
def get_clean_ip(ips):
    try:
        if not ips:
            ips=default_ips

        user_ip=request.remote_addr
        asnres = ipasn.get(user_ip) if ipasn else {'autonomous_system_number':'unknown'}
        asn = asnres['autonomous_system_number']
        ips=re.split('[ \t\r\n;,]+',ips)
        print(ips)
        if any([ip for ip in ips if ip in asn_map.values()]):
            for i in range(0,len(ips),2):
                if asn_map.get(asn,ips[1])== ips[i+1]:
                    return hiddify.get_domain_ip(ips[i])
        else:
            return hiddify.get_domain_ip(random.sample(ips, 1))
        return None
    except Exception as e:
        print(e)
        flash(_("Error! auto cdn ip can not be find, please contact admin."))
    