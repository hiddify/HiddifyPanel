from flask import g
import enum
from hiddifypanel.models import User,Domain,BoolConfig,StrConfig,DomainType,ConfigEnum,get_hconfigs,get_hdomains,hconfig,Proxy
import yaml
def all_proxies():
    # all_cfg= [
    #     'WS Fake vless',
    #     'WS Fake trojan',
    #     'WS Fake vmess',
    #     # 'grpc Fake vless',
    #     # 'grpc Fake trojan',
    #     # 'grpc Fake vmess',
    #     "XTLS direct vless",
    #     "WS direct vless",
    #     "WS direct trojan",
    #     "WS direct vmess",
    #     "WS CDN vless",
    #     "WS CDN trojan",
    #     "WS CDN vmess",
    #     "grpc CDN vless",
    #     "grpc CDN trojan",
    #     "grpc CDN vmess",
    #     "tcp direct vless",
    #     "tcp direct trojan",
    #     "tcp direct vmess",
    #     "h1 direct vless",
    #     "h1 direct vmess",
    #     "faketls direct ss",
    #     "ws direct v2ray",
    #     "ws CDN v2ray"
    # ]
    all_cfg=Proxy.query.filter(Proxy.enable==True).all()
    if not hconfig(ConfigEnum.domain_fronting_domain):
        all_cfg=[c for c in all_cfg if 'Fake' not in c.cdn]
    if not g.is_cdn:
        all_cfg=[c for c in all_cfg if 'CDN' not in c.cdn]
    if not hconfig(ConfigEnum.ssfaketls_enable):
        all_cfg=[c for c in all_cfg if 'faketls' not in c.transport and 'v2ray' not in c.proto]
    if not hconfig(ConfigEnum.vmess_enable):
        all_cfg=[c for c in all_cfg if 'vmess' not in c.proto]

     
    return all_cfg

def proxy_info(name, mode="tls"):
    return "error"
# def proxy_info(name, mode="tls"):
    
#     domain = g.domain
#     hconfigs=get_hconfigs()
#     if mode=="tls":
#         port=443
#         security="tls"
#     elif mode =="http":
#         security = 'http'
#         port == 80
#     elif mode =="kcp":
#         security = 'kcp'
#         port == hconfig(ConfigEnum.kcp_ports).split(",")[0]

#     name_enc = name.replace(" ", "_")+f'_{security}_{domain}_{port}'
#     if hconfig(ConfigEnum.domain_fronting_domain) and  ((security=="http" and hconfig(ConfigEnum.domain_fronting_http_enable)) or (security=="tls" and hconfig(ConfigEnum.domain_fronting_tls_enable))):
#         if name == 'WS Fake vless':
#             return {'name':name_enc,'name':name_enc,'transport': 'ws', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'Fake', 'url': f'vless://{g.user_uuid}@{hconfigs[ConfigEnum.fake_cdn_domain]}:{port}?security={security}&sni={hconfigs[ConfigEnum.fake_cdn_domain]}&type=ws&host={domain}&path=/{hconfigs[ConfigEnum.proxy_path]}/vlessws#{name_enc}'}

#         # if security!="http" and name == 'WS Fake trojan':
#         #     return {'name':name_enc,'transport': 'ws', 'proto': 'trojan', 'security': security, 'port': port, 'mode': 'Fake', 'url': f'trojan://{g.user_uuid}@{hconfigs[ConfigEnum.fake_cdn_domain]}:{port}?security={security}&sni={hconfigs[ConfigEnum.fake_cdn_domain]}&type=ws&host={domain}&path=/{hconfigs[ConfigEnum.proxy_path]}/trojanws#{name_enc}'}
#         if name == 'WS Fake vmess':
#             return {'name':name_enc,'transport': 'ws', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'Fake', 'url': pbase64(f'vmess://{{"v":"2", "ps":"{name_enc}", "add":"{domain}", "port":"{port}", "id":"{g.user_uuid}", "aid":"0", "scy":"auto", "net":"ws", "type":"none", "host":"{domain}", "path":"/{hconfigs[ConfigEnum.proxy_path]}/vmessws", "tls":"{security}", "sni":"{hconfigs[ConfigEnum.fake_cdn_domain]}"}}')}
#         # if name == 'grpc Fake vless':
#         #     return {'name':name_enc,'transport': 'grpc', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'Fake', 'url': f'vless://{g.user_uuid}@{hconfigs[ConfigEnum.fake_cdn_domain]}:{port}?security={security}&sni={domain}&type=grpc&serviceName={hconfigs[ConfigEnum.proxy_path]}-vlgrpc&mode=multi#{name_enc}'}

#         # if security!="http" and name == 'grpc Fake trojan':
#         #     return {'name':name_enc,'transport': 'grpc', 'proto': 'trojan', 'security': security, 'port': port, 'mode': 'Fake', 'url': f'trojan://{g.user_uuid}@{hconfigs[ConfigEnum.fake_cdn_domain]}:{port}?security={security}&sni={domain}&type=grpc&serviceName={hconfigs[ConfigEnum.proxy_path]}-trgrpc&mode=multi#{name_enc}'}

#         # if name == 'grpc Fake vmess':
#         #     return {'name':name_enc,'transport': 'grpc', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'Fake', 'url': pbase64(f'vmess://{{"v":"2", "ps":"{name_enc}", "add":"{hconfigs[ConfigEnum.fake_cdn_domain]}", "port":"{port}", "id":"{g.user_uuid}", "aid":"0", "scy":"auto", "net":"grpc", "type":"multi", "host":"{domain}", "path":"{hconfigs[ConfigEnum.proxy_path]}-vmgrpc", "tls":"{security}", "sni":"{hconfigs[ConfigEnum.fake_cdn_domain]}"}}')}

#     # if hconfig(ConfigEnum.domain_fronting_http_enable):
#     #     if name == 'http Fake vless':
#     #         return {'name':name_enc,'transport': 'ws', 'proto': 'vless', 'security': 'http', 'port': 80, 'mode': 'Fake', 'url': f'vless://{g.user_uuid}@{hconfigs[ConfigEnum.fake_cdn_domain]}:80?security=none&type=ws&host={domain}&path=/{hconfigs[ConfigEnum.proxy_path]}/vlessws#{name_enc}'}
#     #     if name == 'http Fake vmess':
#     #         return {'name':name_enc,'transport': 'ws', 'proto': 'vmess', 'security': 'http', 'port': 80, 'mode': 'Fake', 'url': pbase64(f'vmess://{{"v":"2", "ps":"{name_enc}", "add":"{hconfigs[ConfigEnum.domain_fronting_domain]}", "port":"{port}", "id":"{g.user_uuid}", "aid":"0", "scy":"auto", "net":"ws", "type":"none", "host":"{domain}", "path":"/{hconfigs[ConfigEnum.proxy_path]}/vmessws"}}')}
#     if security=="http" and not hconfig(ConfigEnum.http_proxy_enable):
#         return None
#     if security!="http" and  name == "XTLS direct vless":
#         return {'name':name_enc,'transport': 'tcp', 'proto': 'vless', 'security': 'xtls', 'port': port, 'mode': 'direct', 'url': f'vless://{g.user_uuid}@{{direct_host}}:{port}?flow=xtls-rprx-direct&security=xtls&alpn=h2&sni={domain}&type=tcp#{name_enc}'}
#     if name == "WS direct vless":
#         return {'name':name_enc,'transport': 'ws', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'direct', 'url': f'vless://{g.user_uuid}@{{direct_host}}:{port}?security={security}&sni={domain}&type=ws&alpn=h2&path=/{hconfigs[ConfigEnum.proxy_path]}/vlessws#{name_enc}'}
#     if security!="http" and name == "WS direct trojan":
#         return {'name':name_enc,'transport': 'ws', 'proto': 'trojan', 'security': security, 'port': port, 'mode': 'direct', 'url': f'trojan://{g.user_uuid}@{{direct_host}}:{port}?security={security}&sni={domain}&type=ws&alpn=h2&path=/{hconfigs[ConfigEnum.proxy_path]}/trojanws#{name_enc}'}
#     if name == "WS direct vmess":
#         return {'name':name_enc,'transport': 'ws', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'direct', 'url': pbase64(f'vmess://{{"v":"2", "ps":"{name_enc}", "add":"{{direct_host}}", "port":"{port}", "id":"{g.user_uuid}", "aid":"0", "scy":"auto", "net":"ws", "type":"none", "host":"", "path":"/{hconfigs[ConfigEnum.proxy_path]}/vmessws", "tls":"{security}", "sni":"{domain}","alpn":"h2"}}')}

#     if name == "WS CDN vless":
#         return {'name':name_enc,'transport': 'ws', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'CDN', 'url': f'vless://{g.user_uuid}@{domain}:{port}?security{security}&sni={domain}&type=ws&path=/{hconfigs[ConfigEnum.proxy_path]}/vlessws#{name_enc}'}
#     if security!="http" and name == "WS CDN trojan":
#         return {'name':name_enc,'transport': 'ws', 'proto': 'trojan', 'security': security, 'port': port, 'mode': 'CDN', 'url': f'trojan://{g.user_uuid}@{domain}:{port}?security{security}&sni={domain}&type=ws&path=/{hconfigs[ConfigEnum.proxy_path]}/trojanws#{name_enc}'}
#     if name == "WS CDN vmess":
#         return {'name':name_enc,'transport': 'ws', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'CDN', 'url': pbase64(f'vmess://{{"v":"2", "ps":"{name_enc}", "add":"{domain}", "port":"{port}", "id":"{g.user_uuid}", "aid":"0", "scy":"auto", "net":"ws", "type":"none", "host":"", "path":"/{hconfigs[ConfigEnum.proxy_path]}/vmessws", "tls":"{security}", "sni":"{domain}"}}')}

#     if name == "grpc CDN vless":
#         return {'name':name_enc,'transport': 'grpc', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'CDN', 'url': f'vless://{g.user_uuid}@{{direct_host}}:{port}?security{security}&alpn=h2&sni={domain}&type=grpc&serviceName={hconfigs[ConfigEnum.proxy_path]}-vlgrpc&mode=multi#{name_enc}'}
#     if security!="http" and name == "grpc CDN trojan":
#         return {'name':name_enc,'transport': 'grpc', 'proto': 'trojan', 'security': security, 'port': port, 'mode': 'CDN', 'url': f'trojan://{g.user_uuid}@{{direct_host}}:{port}?security{security}&alpn=h2&sni={domain}&type=grpc&serviceName={hconfigs[ConfigEnum.proxy_path]}-trgrpc&mode=multi#{name_enc}'}
#     if name == "grpc CDN vmess":
#         return {'name':name_enc,'transport': 'grpc', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'CDN', 'url': pbase64(f'vmess://{{"v":"2", "ps":"{name_enc}", "add":"{{direct_host}}", "port":"{port}", "id":"{g.user_uuid}", "aid":"0", "scy":"auto", "net":"grpc", "type":"multi", "host":"", "path":"{hconfigs[ConfigEnum.proxy_path]}-vmgrpc", "tls":"{security}", "sni":"{domain}","alpn":"h2"}}')}

#     if name == "tcp direct vless":
#         return {'name':name_enc,'transport': 'tcp', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'direct', 'url': f'vless://{g.user_uuid}@{{direct_host}}:{port}?security{security}&alpn=h2&sni={domain}&type=tcp#{name_enc}'}
#     if security!="http" and name == "grpc CDN trojan":
#         return {'name':name_enc,'transport': 'tcp', 'proto': 'trojan', 'security': security, 'port': port, 'mode': 'direct', 'url': f'trojan://{g.user_uuid}@{{direct_host}}:{port}?security{security}&alpn=h2&sni={domain}&type=tcp#{name_enc}'}
#     if name == "grpc CDN vmess":
#         return {'name':name_enc,'transport': 'tcp', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'direct', 'url': pbase64(f'vmess://{{"v": "2", "ps": "{name_enc}", "add": "{{direct_host}}", "port": "{port}", "id": "{g.user_uuid}", "aid": "0", "scy": "auto", "net": "tcp", "type":"http", "host": "", "path": "/{hconfigs[ConfigEnum.proxy_path]}/vmtc", "tls": "{security}", "sni": "{domain}","alpn":"h2"}}')}

#     if name == "h1 direct vless":
#         return {'name':name_enc,'transport': 'h1.1', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'direct', 'url': f'vless://{g.user_uuid}@{{direct_host}}:{port}?security{security}&alpn=http/1.1&sni={domain}&alpn=h2&type=tcp&headerType=http&path=/{hconfigs[ConfigEnum.proxy_path]}/vltc#{name_enc}'}
#     if name == "h1 direct vmess":
#         return {'name':name_enc,'transport': 'tcp', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'direct', 'url': pbase64(f'vmess://{{"v": "2", "ps": "{name_enc}", "add": "{{direct_host}}", "port": "{port}", "id": "{g.user_uuid}", "aid": "0", "scy": "auto", "net": "tcp", "type":"http", "host": "", "path": "/{hconfigs[ConfigEnum.proxy_path]}/vmtc", "tls": "{security}", "sni": "{domain}","alpn":"http/1.1"}}')}
#     if security!="http" and name == "faketls direct ss":
#         return {'name':name_enc,'transport': 'faketls', 'proto': 'ss', 'security': security, 'port': port, 'mode': 'direct', 'url': f'ss://chacha20-ietf-poly1305:{{hconfigs[ConfigEnum.ssfaketls_secret]}}@{{direct_host}}:{port}?plugin=obfs-local%3Bobfs%3Dtls%3Bobfs-host%3D{hconfig(ConfigEnum.ssfaketls_fakedomain)}&amp;udp-over-tcp=true#{name_enc}'}
#     if name == "ws direct v2ray":
#         return {'name':name_enc,'transport': 'ws', 'proto': 'v2ray', 'security': security, 'port': port, 'mode': 'direct', 'url': f'ss://chacha20-ietf-poly1305:{{hconfigs[ConfigEnum.ssfaketls_secret]}}@{{direct_host}}:{port}?plugin=v2ray-plugin%3Bmode%3Dwebsocket%3Bpath%3D/{hconfigs[ConfigEnum.proxy_path]}/v2ray/%3Bhost%3D{domain}%3Btls&amp;udp-over-tcp=true#{name_enc}'}
#     if name == "ws CDN v2ray":
#         return {'name':name_enc,'transport': 'ws', 'proto': 'v2ray', 'security': security, 'port': port, 'mode': 'CDN', 'url': f'ss://chacha20-ietf-poly1305:{{hconfigs[ConfigEnum.ssfaketls_secret]}}@{{domain}}:{port}?plugin=v2ray-plugin%3Bmode%3Dwebsocket%3Bpath%3D/{hconfigs[ConfigEnum.proxy_path]}/v2ray/%3Bhost%3D{domain}%3Btls&amp;udp-over-tcp=true#{name_enc}'}

def pbase64(full_str):
    return full_str
    str=full_str.split("vmess://")[1]
    import base64
    resp=base64.b64encode(f'{str}'.encode("utf-8"))
    return "vmess://"+resp.decode()



def make_proxy(proxy):
    model=proxy.l3

    domain = g.domain
    hconfigs=get_hconfigs()
    port=0
    if model=="tls":
        port=443
        l3="tls"
    elif model =="http":
        l3 = 'http'
        port == 80
    elif model =="kcp":
        l3 = 'kcp'
        port == hconfig(ConfigEnum.kcp_ports).split(",")[0]
    
    name=proxy.name   
    is_cdn="CDN" in name
    direct_host=domain if is_cdn else g.direct_host
    
    base={
        'name':name.replace(" ", "_"),#+f'_{l3}_{domain}_{port}',
        'cdn':is_cdn,
        'mode':"CDN" if is_cdn else "direct",
        'l3': l3,
        'port': port,
        'server':domain if is_cdn else g.direct_host,
        'sni':domain,
        'uuid':str(g.user_uuid),
        'proto':proxy.proto,
        'transport':proxy.transport,
        'proxy_path':hconfig(ConfigEnum.proxy_path),
        'alpn':"h2"
    }

    if base["proto"]=="trojan" and l3!="tls":
        return

    if l3=="http" and  "XTLS" in name:
        return None
    if l3=="http" and base["proto"] in ["ss","ssr"]:
        return 
    

    if "FAKE" in name:
        if not hconfig(ConfigEnum.domain_fronting_domain):
            return
        if l3=="http" and not hconfig(ConfigEnum.domain_fronting_http_enable):
            return
        if l3=="tls" and  not hconfig(ConfigEnum.domain_fronting_tls_enable):
            return 
        base['server']=hconfigs[ConfigEnum.domain_fronting_domain]
        base['sni']=hconfigs[ConfigEnum.domain_fronting_domain]
        base["host"]=domain
        base['mode']='Fake'
    elif l3=="http" and not hconfig(ConfigEnum.http_proxy_enable):
        return None    

    ws_path={'vless':f'/{hconfigs[ConfigEnum.proxy_path]}/vlessws',
            'trojan': f'/{hconfigs[ConfigEnum.proxy_path]}/trojanws',
            'vmess':f'/{hconfigs[ConfigEnum.proxy_path]}/vmessws',
            'v2ray':f'/{hconfigs[ConfigEnum.proxy_path]}/v2ray/'
    }
    tcp_path={'vless':f'/{hconfigs[ConfigEnum.proxy_path]}/vltc',
            'trojan': f'/{hconfigs[ConfigEnum.proxy_path]}/trtc',
            'vmess':f'/{hconfigs[ConfigEnum.proxy_path]}/vmtc'
    }
    grpc_service_name={
        'vless':f'{hconfigs[ConfigEnum.proxy_path]}-vlgrpc',
        'vmess':f'{hconfigs[ConfigEnum.proxy_path]}-vmgrpc',
        'trojan': f'{hconfigs[ConfigEnum.proxy_path]}-trgrpc'
    }    

    if base["proto"] in ['v2ray','ss','ssr']:
        base['chipher']='chacha20-ietf-poly1305'
        base['uuid']=f'{hconfig(ConfigEnum.shared_secret)}'

    if base["proto"]=="ssr":
        base["ssr-obfs"]= "tls1.2_ticket_auth"
        base["ssr-protocol"]= "auth_sha1_v4"
        base["fakedomain"]=hconfigs[ConfigEnum.ssr_fakedomain]
        base["mode"]="faketls"
        return base
    elif "faketls" in name:
        base['fakedomain']=hconfig(ConfigEnum.ssfaketls_fakedomain)
        base['mode']='FakeTLS'
        return base
    elif "shadowtls" in name:
        base['fakedomain']=hconfig(ConfigEnum.shadowtls_fakedomain)
        base['mode']='ShadowTLS'
        return base

    if "XTLS" in name:
        return {**base, 'transport': 'tcp', 'l3': 'xtls', 'alpn':'h2','flow':'xtls-rprx-direct'}
    if "tcp" in name:
        base['transport']='tcp'
        base['path']=tcp_path[base["proto"]]
        return base   
    if "WS" in name:
        base['transport']='ws'
        base['path']=ws_path[base["proto"]]
        return base
    if "grpc" in name:
        base['transport']='grpc'
        base['grpc_mode']="multi"
        base['grpc_service_name']=grpc_service_name[base["proto"]]
        return base
    
    if "h1" in name:
        base['transport']= 'tcp'
        base['alpn']='http/1.1'
        return base
    return "error!"


def to_link(proxy):
    if type(proxy) is str:return proxy
    if proxy['proto']=='vmess':
        return pbase64(f'vmess://{{"v":"2", "ps":"{proxy["name"]}", "add":"{proxy["server"]}", "port":"{proxy["port"]}", "id":"{proxy["uuid"]}", "aid":"0", "scy":"auto", "net":"{proxy["transport"]}", "type":"none", "host":"{proxy.get("host")}", "path":"{proxy["path"] if "path" in proxy else ""}", "tls":"{proxy["l3"]}", "sni":"{proxy["sni"]}"}}')
    if proxy['proto']=="ssr":
        baseurl=f'ssr://proxy["encryption"]:{proxy["uuid"]}@{proxy["server"]}:{proxy["port"]}'
        return None
    if proxy['proto'] in ['ss','v2ray']:
        baseurl=f'ss://proxy["encryption"]:{proxy["uuid"]}@{proxy["server"]}:{proxy["port"]}'
        if proxy['mode']=='faketls':
            return f'{baseurl}?plugin=obfs-local%3Bobfs%3Dtls%3Bobfs-host%3D{proxy["fakedomain"]}&amp;udp-over-tcp=true#{proxy["name"]}'
        if proxy['mode']=='shadowtls':
            return f'{baseurl}?plugin=shadow-tls%3Bpassword%3D{proxy["proxy_path"]}%3Bhost%3D{proxy["fakedomain"]}&amp;udp-over-tcp=true#{proxy["name"]}'
        if proxy['proto']=='v2ray':
            return f'{baseurl}?plugin=v2ray-plugin%3Bmode%3Dwebsocket%3Bpath%3D{proxy["path"]}%3Bhost%3D{domain}%3Btls&amp;udp-over-tcp=true#{proxy["name"]}'
    
    infos=f'&alpn={proxy["alpn"]}&sni={proxy["sni"]}&type={proxy["transport"]}'
    infos+=f'&path={proxy["path"]}' if "path" in proxy else ""
    infos+='&host={proxy["host"]}' if "host" in proxy else ""
    infos+=f'#{proxy["name"]}'
    if "grpc"==proxy["mode"]:
        infos+=f'&serviceName={proxy["grpc_service_name"]}&mode={proxy["grpc_mode"]}'
    baseurl=f'{proxy["proto"]}://{proxy["uuid"]}@{proxy["server"]}:{proxy["port"]}'
    if proxy['l3']=='xtls':
        return f'{baseurl}?flow={proxy["flow"]}&security=xtls&type=tcp{infos}'
    if proxy['l3']=='http':
        return f'{baseurl}?security=none{infos}'
    if proxy['l3']=='tls':
        return f'{baseurl}?security=tls{infos}#{proxy["name"]}'
    
def to_clash_yml(proxy):
    return yaml.dump(to_clash(proxy))

def to_clash(proxy):
    if proxy['l3']=="kcp":return
    base={}
    # vmess ws
    base["name"]= proxy["name"]
    base["type"]= proxy["proto"]
    base["server"]= proxy["server"]
    base["port"]=proxy["port"]
    if proxy["proto"]=="ssr":
        base["cipher"]= proxy["chipher"]
        base["password"]= proxy["uuid"]
        base["udp"]= True
        base["obfs"]= proxy["ssr-obfs"]
        base["protocol"]= proxy["ssr-protocol"]
        base["obfs-param"]= proxy["fakedomain"]
        return base
    elif proxy["proto"] in ["ss","v2ray"]:
        base["cipher"]= proxy["chipher"]
        base["password"]= proxy["uuid"]
        base["udp_over_tcp"]= True
        if proxy["transport"]=="faketls":
            base["plugin"]= "obfs"
            base["plugin-opts"]={
                "mode": tls,
                "host": proxy["fakedomain"]
            }
        elif proxy["transport"]=="shadowtls":
            base["plugin"]= "shadow-tls"
            base["plugin-opts"]={
                "host": proxy["fakedomain"],
                "password": proxy["proxy_path"]
            }
            
        elif proxy["proto"]=="v2ray":
            base["plugin"]= "v2ray-plugin"
            base["plugin-opts"]={
                "mode": "websocket",
                "tls": proxy["l3"]=="tls",
                "skip-cert-verify": proxy["mode"]=="FAKE",
                "host": proxy['sni'],
                "path": proxy["path"]
            }
        return base
    elif proxy["proto"]=="trojan":
        base["password"]=proxy["uuid"]
        base["sni"]= proxy["sni"]
    else:
        base["uuid"]= proxy["uuid"]
        base["servername"]= proxy["sni"]
        base["tls"]= proxy["l3"]=="tls"
    if "proxy"=="XTLS":
        base["flow"]= "xtls-rprx-direct"
        base["flow-show"]= True

    if proxy["proto"]=="vmess":
        base["alterId"]= 0
        base["cipher"]= "auto"
    base["udp"]= True
    
    base["skip-cert-verify"]= proxy["mode"]=="FAKE"
    
    
    base["network"]= proxy["transport"]
    
    if base["network"]=="ws":
        base["ws-opts"]={
            "path":proxy["path"]
        }
        if "host" in proxy:
            base["ws-opts"]["headers"]={"Host":proxy["host"]}
    # if proxy["transport"]=="tcp" and proxy["l3"]=="http":
    #     base["network"]="http"
    #     base["http-opts"]={
    #         "path":proxy["path"]
    #     }
        
    if base["network"]=="grpc":
        base["grpc-opts"]={
        "grpc-service-name":proxy["grpc_service_name"]
        }

    return base
    


def get_all_clash_configs():
    allp=[]
    for type in all_proxies():
        pinfo=make_proxy(type)
        if pinfo!=None:
            clash=to_clash(pinfo)
            if clash:
                allp.append(clash)
    
    return yaml.dump({"proxies":allp},sort_keys=False)
