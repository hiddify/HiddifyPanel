from flask import g,request
import enum
from hiddifypanel.models import *
import yaml
import json
from hiddifypanel.panel import hiddify


def all_proxies(child_id=0):
    all_proxies = hiddify.get_available_proxies(child_id)
    all_proxies = [p for p in all_proxies if p.enable]
    # all_cfg=Proxy.query.filter(Proxy.enable==True).all()
    # if not hconfig(ConfigEnum.domain_fronting_domain):
    #     all_cfg=[c for c in all_cfg if 'Fake' not in c.cdn]
    # if not g.is_cdn:
    #     all_cfg=[c for c in all_cfg if 'CDN' not in c.cdn]
    # if not hconfig(ConfigEnum.ssfaketls_enable):
    #     all_cfg=[c for c in all_cfg if 'faketls' not in c.transport and 'v2ray' not in c.proto]
    # if not hconfig(ConfigEnum.vmess_enable):
    #     all_cfg=[c for c in all_cfg if 'vmess' not in c.proto]

    return all_proxies


def proxy_info(name, mode="tls"):
    return "error"


def pbase64(full_str):
    return full_str
    str = full_str.split("vmess://")[1]
    import base64
    resp = base64.b64encode(f'{str}'.encode("utf-8"))
    return "vmess://"+resp.decode()


def make_proxy(proxy, domain_db, phttp=80, ptls=443):
    if type(phttp) == str:
        phttp = int(phttp) if phttp != "None" else None
    if type(ptls) == str:
        ptls = int(ptls) if ptls != "None" else None
    l3 = proxy.l3

    domain = domain_db.domain

    child_id = domain_db.child_id
    hconfigs = get_hconfigs(child_id)
    port = 0

    if l3 in [ProxyL3.tls, ProxyL3.tls_h2, ProxyL3.tls_h2_h1]:
        port = ptls
    elif l3 == "http":
        port = phttp
    elif l3 == "kcp":
        port = hconfigs[ConfigEnum.kcp_ports].split(",")[0]
    elif l3 == "tuic":
        port = hconfigs[ConfigEnum.tuic_port].split(",")[0]

    if not port:
        return
    name = proxy.name

    is_cdn = ProxyCDN.CDN in proxy.cdn
    if is_cdn and domain_db.mode not in  [DomainType.cdn,DomainType.auto_cdn_ip]:
        # print("cdn proxy not in cdn domain", domain, name)
        return
    if not is_cdn and domain_db.mode in  [DomainType.cdn,DomainType.auto_cdn_ip]:
        # print("not cdn proxy  in cdn domain", domain, name, proxy.cdn)
        return

    cdn_forced_host = domain_db.cdn_ip or domain_db.domain

    base = {
        'name': name.replace(" ", "_"),
        'cdn': is_cdn,
        'mode': "CDN" if is_cdn else "direct",
        'l3': l3,
        'host': domain,
        'port': port,
        'server': cdn_forced_host,
        'sni': domain,
        'uuid': str(g.user_uuid),
        'proto': proxy.proto,
        'transport': proxy.transport,
        'proxy_path': hconfigs[ConfigEnum.proxy_path],
        'alpn': "h2" if proxy.l3 == 'tls_h2' else 'h2,http/1.1' if proxy.l3 == 'tls_h2_h1' else "http/1.1",
        'extra_info': f'{domain_db.alias or domain}',
        'fingerprint': hconfigs[ConfigEnum.utls],
        'allow_insecure': domain_db.mode == DomainType.fake or "Fake" in proxy.cdn,
        'dbe':proxy,
        'dbdomain':domain_db
    }

    if base["proto"] == "trojan" and "tls" not in l3:
        return

    if l3 == "http" and "XTLS" in proxy.transport:
        return None
    if l3 == "http" and base["proto"] in ["ss", "ssr"]:
        return
    if proxy.proto in ProxyProto.vmess:
        base['cipher']="chacha20-poly1305"
    if "Fake" in proxy.cdn:
        if not hconfigs[ConfigEnum.domain_fronting_domain]:
            return
        if l3 == "http" and not hconfigs[ConfigEnum.domain_fronting_http_enable]:
            return
        if l3 == "tls" and not hconfigs[ConfigEnum.domain_fronting_tls_enable]:
            return
        base['server'] = hconfigs[ConfigEnum.domain_fronting_domain]
        base['sni'] = hconfigs[ConfigEnum.domain_fronting_domain]
        # base["host"]=domain
        base['mode'] = 'Fake'

    elif l3 == "http" and not hconfigs[ConfigEnum.http_proxy_enable]:
        return None
    path = {
        'vless': f'{hconfigs[ConfigEnum.path_vless]}',
        'trojan': f'{hconfigs[ConfigEnum.path_trojan]}',
        'vmess': f'{hconfigs[ConfigEnum.path_vmess]}',
        'ss': f'{hconfigs[ConfigEnum.path_ss]}',
        'v2ray': f'{hconfigs[ConfigEnum.path_ss]}'
    }

    if base["proto"] in ['v2ray', 'ss', 'ssr']:
        base['cipher'] = 'chacha20-ietf-poly1305'
        if "shadowtls" not in proxy.transport:
            base['uuid'] = f'{hconfigs[ConfigEnum.shared_secret]}'

    if base["proto"] == "ssr":
        base["ssr-obfs"] = "tls1.2_ticket_auth"
        base["ssr-protocol"] = "auth_sha1_v4"
        base["fakedomain"] = hconfigs[ConfigEnum.ssr_fakedomain]
        base["mode"] = "FakeTLS"
        return base
    elif "faketls" in proxy.transport:
        base['fakedomain'] = hconfigs[ConfigEnum.ssfaketls_fakedomain]
        base['mode'] = 'FakeTLS'
        return base
    elif "shadowtls" in proxy.transport:

        base['fakedomain'] = hconfigs[ConfigEnum.shadowtls_fakedomain]
        base['mode'] = 'ShadowTLS'
        return base

    if "XTLS" in proxy.transport:
        base['flow'] = 'xtls-rprx-vision'
        return {**base, 'transport': 'tcp', 'l3': 'xtls'}
    if "tcp" in proxy.transport:
        base['transport'] = 'tcp'
        base['path'] = f'/{path[base["proto"]]}{hconfigs[ConfigEnum.path_tcp]}'
        return base
    if proxy.transport in ["ws", "WS"]:
        base['transport'] = 'ws'
        base['path'] = f'/{path[base["proto"]]}{hconfigs[ConfigEnum.path_ws]}'
        base["host"] = domain
        return base

    if proxy.transport == "grpc":
        base['transport'] = 'grpc'
        base['grpc_mode'] = "multi"
        base['grpc_service_name'] = f'{path[base["proto"]]}{hconfigs[ConfigEnum.path_grpc]}'
        base['path'] = base['grpc_service_name']
        return base

    if "h1" in proxy.transport:
        base['transport'] = 'tcp'
        base['alpn'] = 'http/1.1'
        return base
    return {'name': name, 'error': True, 'proto': proxy.proto}


def to_link(proxy):
    if 'error' in proxy:
        return proxy

    name_link = proxy["name"]+"_"+proxy['extra_info']
    if proxy['proto'] == 'vmess':
        # print(proxy)
        vmess_type = None
        if proxy["transport"] == 'tcp':
            vmess_type = 'http'
        if 'grpc_mode' in proxy:
            vmess_type = proxy['grpc_mode']
        vmess_data = {"v": "2",
                      "ps": name_link,
                      "add": proxy['server'],
                      "port": proxy['port'],
                      "id": proxy["uuid"],
                      "aid": "0",
                      "scy": proxy['cipher'],
                      "net": proxy["transport"],
                      "type": vmess_type,
                      "host": proxy.get("host", ""),
                      "path": proxy["path"] if "path" in proxy else "",
                      "tls": "tls" if "tls" in proxy["l3"] else "",
                      "sni": proxy["sni"],
                      "fp": proxy["fingerprint"]
                      }

        return pbase64(f'vmess://{json.dumps(vmess_data)}')
    if proxy['proto'] == "ssr":
        baseurl = f'ssr://proxy["encryption"]:{proxy["uuid"]}@{proxy["server"]}:{proxy["port"]}'
        return None
    if proxy['proto'] in ['ss', 'v2ray']:
        baseurl = f'ss://proxy["encryption"]:{proxy["uuid"]}@{proxy["server"]}:{proxy["port"]}'
        if proxy['mode'] == 'faketls':
            return f'{baseurl}?plugin=obfs-local%3Bobfs%3Dtls%3Bobfs-host%3D{proxy["fakedomain"]}&amp;udp-over-tcp=true#{name_link}'
        if proxy['mode'] == 'shadowtls':
            return f'{baseurl}?plugin=shadow-tls%3Bpassword%3D{proxy["proxy_path"]}%3Bhost%3D{proxy["fakedomain"]}&amp;udp-over-tcp=true#{name_link}'
        if proxy['proto'] == 'v2ray':
            return f'{baseurl}?plugin=v2ray-plugin%3Bmode%3Dwebsocket%3Bpath%3D{proxy["path"]}%3Bhost%3D{proxy["host"]}%3Btls&amp;udp-over-tcp=true#{name_link}'

    infos = f'&sni={proxy["sni"]}&type={proxy["transport"]}'

    infos += f"&alpn={proxy['alpn']}"

    # infos+=f'&alpn={proxy["alpn"]}'
    infos += f'&path={proxy["path"]}' if "path" in proxy else ""
    infos += f'&host={proxy["host"]}' if "host" in proxy else ""
    if "grpc" == proxy["transport"]:
        infos += f'&serviceName={proxy["grpc_service_name"]}&mode={proxy["grpc_mode"]}'
    if 'vless' == proxy['proto']:
        infos += "&encryption=none"
    if proxy.get('fingerprint','none')!='none':
        infos += "&fp="+proxy['fingerprint']
    if proxy['l3'] != 'quic':
        infos += '&headerType=None'  # if not quic
    if proxy['mode'] == 'Fake' or proxy['allow_insecure']:
        infos += "&allowInsecure=true"

    infos += f'#{name_link}'
    baseurl = f'{proxy["proto"]}://{proxy["uuid"]}@{proxy["server"]}:{proxy["port"]}'
    if 'xtls' == proxy['l3']:
        return f'{baseurl}?flow={proxy["flow"]}&security=tls&type=tcp{infos}'
    if proxy['l3'] == 'http':
        return f'{baseurl}?security=none{infos}'
    if 'tls' in proxy['l3']:
        return f'{baseurl}?security=tls{infos}'


def to_clash_yml(proxy):
    return yaml.dump(to_clash(proxy))


def to_clash(proxy, meta_or_normal):
    if proxy['l3'] == "kcp":
        return
    if proxy.get('flow', '') == "xtls-rprx-vision":
        return
    if meta_or_normal == "normal":
        if proxy['proto'] == "vless":
            return
        if proxy['l3'] == "xtls":
            return
        if proxy['transport'] == "shadowtls":
            return
    if proxy['l3']==ProxyL3.tls_h2 and proxy['proto'] in [ProxyProto.vmess,ProxyProto.vless] and proxy['dbe'].cdn==ProxyCDN.direct:
        return
    base = {}
    # vmess ws
    base["name"] = f"""{proxy["name"]} {proxy['extra_info']} {proxy['port']} {proxy["dbdomain"].id}"""
    base["type"] = str(proxy["proto"])
    base["server"] = proxy["server"]
    base["port"] = proxy["port"]
    base['alpn'] = proxy['alpn'].split(',')
    if proxy["proto"] == "ssr":
        base["cipher"] = proxy["cipher"]
        base["password"] = proxy["uuid"]
        base["udp"] = True
        base["obfs"] = proxy["ssr-obfs"]
        base["protocol"] = proxy["ssr-protocol"]
        base["obfs-param"] = proxy["fakedomain"]
        return base
    elif proxy["proto"] in ["ss", "v2ray"]:
        base["cipher"] = proxy["cipher"]
        base["password"] = proxy["uuid"]
        base["udp_over_tcp"] = True
        if proxy["transport"] == "faketls":
            base["plugin"] = "obfs"
            base["plugin-opts"] = {
                "mode": 'tls',
                "host": proxy["fakedomain"]
            }
        elif proxy["transport"] == "shadowtls":
            base["plugin"] = "shadow-tls"
            base["plugin-opts"] = {
                "host": proxy["fakedomain"],
                "password": proxy["proxy_path"]
            }

        elif proxy["proto"] == "v2ray":
            base["plugin"] = "v2ray-plugin"
            base["type"] = "ss"
            base["plugin-opts"] = {
                "mode": "websocket",
                "tls": "tls" in proxy["l3"] ,
                "skip-cert-verify": proxy["mode"] == "Fake" or proxy['allow_insecure'],
                "host": proxy['sni'],
                "path": proxy["path"]
            }
        return base
    elif proxy["proto"] == "trojan":
        base["password"] = proxy["uuid"]
        base["sni"] = proxy["sni"]

    else:
        base["uuid"] = proxy["uuid"]
        base["servername"] = proxy["sni"]
        base["tls"] = "tls" in proxy["l3"]
    # if meta_or_normal == "meta":
    #     base['client-fingerprint'] = proxy['fingerprint']
    if "xtls" == proxy['l3']:
        base["flow"] = proxy['flow']
        base["flow-show"] = True

    if proxy["proto"] == "vmess":
        base["alterId"] = 0
        base["cipher"] = proxy["cipher"]
    base["udp"] = True

    base["skip-cert-verify"] = proxy["mode"] == "Fake"

    base["network"] = proxy["transport"]

    if base["network"] == "ws":
        base["ws-opts"] = {
            "path": proxy["path"]
        }
        if "host" in proxy:
            base["ws-opts"]["headers"] = {"Host": proxy["host"]}

    if base["network"] == "tcp" and proxy['alpn'] != 'h2':
        # if proxy['proto']=='vless':
        base["network"] = "http"

        if "path" in proxy:
            base["http-opts"] = {
                "path": [proxy["path"]]
            }
            if 'host' in proxy:
                base["http-opts"]["host"] = [proxy["host"]]
    if base["network"] == "tcp" and proxy['alpn'] == 'h2':
        base["network"] = "h2"

        if "path" in proxy:
            base["h2-opts"] = {
                "path": proxy["path"]
            }
            if 'host' in proxy:
                base["h2-opts"]["host"] = [proxy["host"]]
    if base["network"] == "grpc":
        base["grpc-opts"] = {
            "grpc-service-name": proxy["grpc_service_name"]
        }

    return base



def get_clash_config_names(meta_or_normal, domains):
    allphttp=[p for p in request.args.get("phttp","").split(',') if p]
    allptls=[p for p in request.args.get("ptls","").split(',') if p]
    
    allp = []
    for d in domains:
        hconfigs = get_hconfigs(d.child_id)
        for t in (['http', 'tls'] if hconfigs[ConfigEnum.http_proxy_enable] else ['tls']):

            for port in hconfigs[ConfigEnum.http_ports if t == 'http' else ConfigEnum.tls_ports].split(','):

                phttp = port if t == 'http' else None
                ptls = port if t == 'tls' else None
                if phttp and len(allphttp) and phttp not in allphttp:
                    continue
                if ptls and len(allptls) and ptls not in allptls:
                    continue

                for type in all_proxies(d.child_id):
                    pinfo = make_proxy(type, d, phttp=phttp, ptls=ptls)
                    if pinfo != None:
                        clash = to_clash(pinfo, meta_or_normal)
                        if clash:
                            allp.append(clash['name'])

    return yaml.dump(allp, sort_keys=False)


def get_all_clash_configs(meta_or_normal, domains):
    allphttp=[p for p in request.args.get("phttp","").split(',') if p]
    allptls=[p for p in request.args.get("ptls","").split(',') if p]
    
    allp = []
    for d in domains:
        hconfigs = get_hconfigs(d.child_id)
        for t in (['http', 'tls'] if hconfigs[ConfigEnum.http_proxy_enable] else ['tls']):

            for port in hconfigs[ConfigEnum.http_ports if t == 'http' else ConfigEnum.tls_ports].split(','):

                phttp = port if t == 'http' else None
                ptls = port if t == 'tls' else None
                if phttp and len(allphttp) and phttp not in allphttp:
                    continue
                if ptls and len(allptls) and ptls not in allptls:
                    continue

                for type in all_proxies(d.child_id):
                    pinfo = make_proxy(type, d, phttp=phttp, ptls=ptls)
                    if pinfo != None:
                        clash = to_clash(pinfo, meta_or_normal)
                        if clash:
                            allp.append(clash)

    return yaml.dump({"proxies": allp}, sort_keys=False)
