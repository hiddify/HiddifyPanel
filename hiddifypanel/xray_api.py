import xtlsapi
from hiddifypanel.models import  *

def get_xray_client():
    if hconfig(ConfigEnum.is_parent):
        return
    return xtlsapi.XrayClient('127.0.0.1', 10085)
    
def get_enabled_users():
    if hconfig(ConfigEnum.is_parent):
        return
    xray_client=get_xray_client()
    users=User.query.all()
    t="xtls"
    protocol="vless"
    enabled={}
    for u in users:
        uuid=u.uuid
        try:
            xray_client.add_client(t,f'{uuid}', f'{uuid}@hiddify.com',protocol=protocol,flow='xtls-rprx-vision',alter_id=0,cipher='chacha20_poly1305')
            xray_client.remove_client(t,f'{uuid}@hiddify.com')
            enabled[uuid]=0            
        except xtlsapi.exceptions.EmailAlreadyExists as e:
            enabled[uuid]=1
        except Exception as e:
            print(f"error {e}")
            enabled[uuid]=e
    return enabled

def get_inbound_tags():
    if hconfig(ConfigEnum.is_parent):
        return
    try:
        xray_client=get_xray_client()
        inbounds= [inb.name.split(">>>")[1] for inb in xray_client.stats_query('inbound')]
        print(f"Success in get inbound tags {inbounds}" )
    except Exception as e:
        print(f"error in get inbound tags {e}" )
        inbounds=[]
    return inbounds
def add_client(uuid):
    if hconfig(ConfigEnum.is_parent):
        return
    xray_client=get_xray_client()
    tags=get_inbound_tags()
    for t in tags:
        try:
            proto_map={
                'vless':'vless',
                'xtls':'vless',
                'quic':'vless',
                'trojan':'trojan',
                'vmess':'vmess',
                'ss':'shadowsocks',
                'v2ray':'shadowsocks',
                'kcp':'vless',
                'dispatcher':'trojan',
            }
            for p,protocol in proto_map.items():
                if p in t:
                    xray_client.add_client(t,f'{uuid}', f'{uuid}@hiddify.com',protocol=protocol,flow='xtls-rprx-vision',alter_id=0,cipher='chacha20_poly1305')
                    print(f"Success add  {uuid} {t}")
        except Exception as e:
            print(f"error in add  {uuid} {t} {e}" )
            pass

def remove_client(uuid):
    if hconfig(ConfigEnum.is_parent):
        return
    xray_client=get_xray_client()
    tags=get_inbound_tags()
    
    for t in tags:
        try:
            xray_client.remove_client(t, f'{uuid}@hiddify.com')
            print(f"Success remove  {uuid} {t}")
        except Exception as e:
            print(f"error in remove  {uuid} {t} {e}" )
            pass        

def get_usage(uuid,reset=False):
    if hconfig(ConfigEnum.is_parent):
        return
    xray_client=get_xray_client()
    d = xray_client.get_client_download_traffic(f'{uuid}@hiddify.com',reset=reset)
    u = xray_client.get_client_upload_traffic(f'{uuid}@hiddify.com',reset=reset)
    print(f"Success {uuid} d={d} u={u}" )
    if d is None:
        return u
    if u is None:
        return d
    return d+u