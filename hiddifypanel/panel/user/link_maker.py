from flask import g
import enum
from hiddifypanel.models import User,Domain,BoolConfig,StrConfig,DomainType,ConfigEnum,get_hconfigs,get_hdomains,hconfig

def all_proxies():
    all_cfg= [
        'WS FakeCDN vless',
        'WS FakeCDN trojan',
        'WS FakeCDN vmess',
        'grpc FakeCDN vless',
        'grpc FakeCDN trojan',
        'grpc FakeCDN vmess',
        'http FakeCDN vless',
        'http FakeCDN vmess',
        "XTLS direct vless",
        "WS direct vless",
        "WS direct trojan",
        "WS direct vmess",
        "WS CDN vless",
        "WS CDN trojan",
        "WS CDN vmess",
        "grpc CDN vless",
        "grpc CDN trojan",
        "grpc CDN vmess",
        "tcp direct vless",
        "grpc CDN trojan",
        "grpc CDN vmess",
        "h1 direct vless",
        "h1 direct vmess",
        "faketls direct ss",
        "ws direct v2ray",
        "ws CDN v2ray"
    ]
    
    if not hconfig(ConfigEnum.fake_cdn_domain):
        all_cfg=[c for c in all_cfg if 'FakeCDN' not in c]
    if not g.is_cdn:
        all_cfg=[c for c in all_cfg if ' CDN' not in c]
    if not hconfig(ConfigEnum.ssfaketls_enable):
        all_cfg=[c for c in all_cfg if 'faketls' not in c and 'v2ray' not in c]
    if not hconfig(ConfigEnum.vmess_enable):
        all_cfg=[c for c in all_cfg if 'vmess' not in c]
        
    return all_cfg

def proxy_info(name, port=443, security="tls"):
    
    domain = g.domain
    hconfigs=get_hconfigs()
    security = 'http' if port == 80 else security

    name_enc = name.replace(" ", "_")+f'_{security}_{domain}_{port}'
    if name == 'WS FakeCDN vless':
        return {'transport': 'ws', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'FakeCDN', 'url': f'vless://{g.user_uuid}@{hconfigs[ConfigEnum.fake_cdn_domain]}:{port}?security={security}&sni={hconfigs[ConfigEnum.fake_cdn_domain]}&type=ws&host={domain}&path=/{hconfigs[ConfigEnum.proxy_path]}/vlessws#{name_enc}'}

    if security!="http" and name == 'WS FakeCDN trojan':
        return {'transport': 'ws', 'proto': 'trojan', 'security': security, 'port': port, 'mode': 'FakeCDN', 'url': f'trojan://{g.user_uuid}@{hconfigs[ConfigEnum.fake_cdn_domain]}:{port}?security={security}&sni={hconfigs[ConfigEnum.fake_cdn_domain]}&type=ws&host={domain}&path=/{hconfigs[ConfigEnum.proxy_path]}/trojanws#{name_enc}'}
    if name == 'WS FakeCDN vmess':
        return {'transport': 'ws', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'FakeCDN', 'url': pbase64(f'vmess://{{"v":"2", "ps":"{name_enc}", "add":"{domain}", "port":"{port}", "id":"{g.user_uuid}", "aid":"0", "scy":"auto", "net":"ws", "type":"none", "host":"{domain}", "path":"/{hconfigs[ConfigEnum.proxy_path]}/vmessws", "tls":"{security}", "sni":"{hconfigs[ConfigEnum.fake_cdn_domain]}"}}')}
    if name == 'grpc FakeCDN vless':
        return {'transport': 'grpc', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'FakeCDN', 'url': f'vless://{g.user_uuid}@{hconfigs[ConfigEnum.fake_cdn_domain]}:{port}?security={security}&sni={domain}&type=grpc&serviceName={hconfigs[ConfigEnum.proxy_path]}-vlgrpc&mode=multi#{name_enc}'}

    if security!="http" and name == 'grpc FakeCDN trojan':
        return {'transport': 'grpc', 'proto': 'trojan', 'security': security, 'port': port, 'mode': 'FakeCDN', 'url': f'trojan://{g.user_uuid}@{hconfigs[ConfigEnum.fake_cdn_domain]}:{port}?security={security}&sni={domain}&type=grpc&serviceName={hconfigs[ConfigEnum.proxy_path]}-trgrpc&mode=multi#{name_enc}'}
    if name == 'grpc FakeCDN vmess':
        return {'transport': 'grpc', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'FakeCDN', 'url': pbase64(f'vmess://{{"v":"2", "ps":"{name_enc}", "add":"{hconfigs[ConfigEnum.fake_cdn_domain]}", "port":"{port}", "id":"{g.user_uuid}", "aid":"0", "scy":"auto", "net":"grpc", "type":"multi", "host":"{domain}", "path":"{hconfigs[ConfigEnum.proxy_path]}-vmgrpc", "tls":"{security}", "sni":"{hconfigs[ConfigEnum.fake_cdn_domain]}"}}')}

    if name == 'http FakeCDN vless':
        return {'transport': 'ws', 'proto': 'vless', 'security': 'http', 'port': 80, 'mode': 'FakeCDN', 'url': f'vless://{g.user_uuid}@{hconfigs[ConfigEnum.fake_cdn_domain]}:80?security=none&type=ws&host={domain}&path=/{hconfigs[ConfigEnum.proxy_path]}/vlessws#{name_enc}'}
    if name == 'http FakeCDN vmess':
        return {'transport': 'ws', 'proto': 'vmess', 'security': 'http', 'port': 80, 'mode': 'FakeCDN', 'url': pbase64(f'vmess://{{"v":"2", "ps":"{name_enc}", "add":"{hconfigs[ConfigEnum.fake_cdn_domain]}", "port":"{port}", "id":"{g.user_uuid}", "aid":"0", "scy":"auto", "net":"ws", "type":"none", "host":"{domain}", "path":"/{hconfigs[ConfigEnum.proxy_path]}/vmessws"}}')}

    if name == "XTLS direct vless":
        return {'transport': 'tcp', 'proto': 'vless', 'security': 'xtls', 'port': port, 'mode': 'direct', 'url': f'vless://{g.user_uuid}@{{direct_host}}:{port}?flow=xtls-rprx-direct&security=xtls&alpn=h2&sni={domain}&type=tcp#{name_enc}'}
    if name == "WS direct vless":
        return {'transport': 'ws', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'direct', 'url': f'vless://{g.user_uuid}@{{direct_host}}:{port}?security={security}&sni={domain}&type=ws&alpn=h2&path=/{hconfigs[ConfigEnum.proxy_path]}/vlessws#{name_enc}'}
    if security!="http" and name == "WS direct trojan":
        return {'transport': 'ws', 'proto': 'trojan', 'security': security, 'port': port, 'mode': 'direct', 'url': f'trojan://{g.user_uuid}@{{direct_host}}:{port}?security={security}&sni={domain}&type=ws&alpn=h2&path=/{hconfigs[ConfigEnum.proxy_path]}/trojanws#{name_enc}'}
    if name == "WS direct vmess":
        return {'transport': 'ws', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'direct', 'url': pbase64(f'vmess://{{"v":"2", "ps":"{name_enc}", "add":"{{direct_host}}", "port":"{port}", "id":"{g.user_uuid}", "aid":"0", "scy":"auto", "net":"ws", "type":"none", "host":"", "path":"/{hconfigs[ConfigEnum.proxy_path]}/vmessws", "tls":"{security}", "sni":"{domain}","alpn":"h2"}}')}

    if name == "WS CDN vless":
        return {'transport': 'ws', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'CDN', 'url': f'vless://{g.user_uuid}@{domain}:{port}?security{security}&sni={domain}&type=ws&path=/{hconfigs[ConfigEnum.proxy_path]}/vlessws#{name_enc}'}
    if security!="http" and name == "WS CDN trojan":
        return {'transport': 'ws', 'proto': 'trojan', 'security': security, 'port': port, 'mode': 'CDN', 'url': f'trojan://{g.user_uuid}@{domain}:{port}?security{security}&sni={domain}&type=ws&path=/{hconfigs[ConfigEnum.proxy_path]}/trojanws#{name_enc}'}
    if name == "WS CDN vmess":
        return {'transport': 'ws', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'CDN', 'url': pbase64(f'vmess://{{"v":"2", "ps":"{name_enc}", "add":"{domain}", "port":"{port}", "id":"{g.user_uuid}", "aid":"0", "scy":"auto", "net":"ws", "type":"none", "host":"", "path":"/{hconfigs[ConfigEnum.proxy_path]}/vmessws", "tls":"{security}", "sni":"{domain}"}}')}

    if name == "grpc CDN vless":
        return {'transport': 'grpc', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'CDN', 'url': f'vless://{g.user_uuid}@{{direct_host}}:{port}?security{security}&alpn=h2&sni={domain}&type=grpc&serviceName={hconfigs[ConfigEnum.proxy_path]}-vlgrpc&mode=multi#{name_enc}'}
    if security!="http" and name == "grpc CDN trojan":
        return {'transport': 'grpc', 'proto': 'trojan', 'security': security, 'port': port, 'mode': 'CDN', 'url': f'trojan://{g.user_uuid}@{{direct_host}}:{port}?security{security}&alpn=h2&sni={domain}&type=grpc&serviceName={hconfigs[ConfigEnum.proxy_path]}-trgrpc&mode=multi#{name_enc}'}
    if name == "grpc CDN vmess":
        return {'transport': 'grpc', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'CDN', 'url': pbase64(f'vmess://{{"v":"2", "ps":"{name_enc}", "add":"{{direct_host}}", "port":"{port}", "id":"{g.user_uuid}", "aid":"0", "scy":"auto", "net":"grpc", "type":"multi", "host":"", "path":"{hconfigs[ConfigEnum.proxy_path]}-vmgrpc", "tls":"{security}", "sni":"{domain}","alpn":"h2"}}')}

    if name == "tcp direct vless":
        return {'transport': 'tcp', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'direct', 'url': f'vless://{g.user_uuid}@{{direct_host}}:{port}?security{security}&alpn=h2&sni={domain}&type=tcp#{name_enc}'}
    if security!="http" and name == "grpc CDN trojan":
        return {'transport': 'tcp', 'proto': 'trojan', 'security': security, 'port': port, 'mode': 'direct', 'url': f'trojan://{g.user_uuid}@{{direct_host}}:{port}?security{security}&alpn=h2&sni={domain}&type=tcp#{name_enc}'}
    if name == "grpc CDN vmess":
        return {'transport': 'tcp', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'direct', 'url': pbase64(f'vmess://{{"v": "2", "ps": "{name_enc}", "add": "{{direct_host}}", "port": "{port}", "id": "{g.user_uuid}", "aid": "0", "scy": "auto", "net": "tcp", "type":"http", "host": "", "path": "/{hconfigs[ConfigEnum.proxy_path]}/vmtc", "tls": "{security}", "sni": "{domain}","alpn":"h2"}}')}

    if name == "h1 direct vless":
        return {'transport': 'h1', 'proto': 'vless', 'security': security, 'port': port, 'mode': 'direct', 'url': f'vless://{g.user_uuid}@{{direct_host}}:{port}?security{security}&alpn=http/1.1&sni={domain}&alpn=h2&type=tcp&headerType=http&path=/{hconfigs[ConfigEnum.proxy_path]}/vltc#{name_enc}'}
    if name == "h1 direct vmess":
        return {'transport': 'tcp', 'proto': 'vmess', 'security': security, 'port': port, 'mode': 'direct', 'url': pbase64(f'vmess://{{"v": "2", "ps": "{name_enc}", "add": "{{direct_host}}", "port": "{port}", "id": "{g.user_uuid}", "aid": "0", "scy": "auto", "net": "tcp", "type":"http", "host": "", "path": "/{hconfigs[ConfigEnum.proxy_path]}/vmtc", "tls": "{security}", "sni": "{domain}","alpn":"http/1.1"}}')}
    if security!="http" and name == "faketls direct ss":
        return {'transport': 'faketls', 'proto': 'ss', 'security': security, 'port': port, 'mode': 'direct', 'url': f'ss://chacha20-ietf-poly1305:{{hconfigs[ConfigEnum.ssfaketls_secret]}}@{{direct_host}}:{port}?plugin=obfs-local%3Bobfs%3Dtls%3Bobfs-host%3D{hconfig(ConfigEnum.ssfaketls_fakedomain)}&amp;udp-over-tcp=true#{name_enc}'}
    if name == "ws direct v2ray":
        return {'transport': 'ws', 'proto': 'v2ray', 'security': security, 'port': port, 'mode': 'direct', 'url': f'ss://chacha20-ietf-poly1305:{{hconfigs[ConfigEnum.ssfaketls_secret]}}@{{direct_host}}:{port}?plugin=v2ray-plugin%3Bmode%3Dwebsocket%3Bpath%3D/{hconfigs[ConfigEnum.proxy_path]}/v2ray/%3Bhost%3D{domain}%3Btls&amp;udp-over-tcp=true#{name_enc}'}
    if name == "ws CDN v2ray":
        return {'transport': 'ws', 'proto': 'v2ray', 'security': security, 'port': port, 'mode': 'CDN', 'url': f'ss://chacha20-ietf-poly1305:{{hconfigs[ConfigEnum.ssfaketls_secret]}}@{{domain}}:{port}?plugin=v2ray-plugin%3Bmode%3Dwebsocket%3Bpath%3D/{hconfigs[ConfigEnum.proxy_path]}/v2ray/%3Bhost%3D{domain}%3Btls&amp;udp-over-tcp=true#{name_enc}'}

def pbase64(full_str):
    return full_str
    str=full_str.split("vmess://")[1]
    import base64
    resp=base64.b64encode(f'{str}'.encode("utf-8"))
    return "vmess://"+resp.decode()
