import yaml
from hiddifypanel.models import ProxyCDN, ProxyL3, ProxyProto, ProxyTransport, Domain
from hiddifypanel import hutils
# https://wiki.metacubex.one/en/


def get_clash_config_names(meta_or_normal, domains: list[Domain]):
    allp = []
    for pinfo in hutils.proxy.get_valid_proxies(domains):
        clash = to_clash(pinfo, meta_or_normal)
        if 'msg' not in clash:
            allp.append(clash['name'])

    return yaml.dump(allp, sort_keys=False)


def get_all_clash_configs(meta_or_normal, domains: list[Domain]):
    allp = []
    for pinfo in hutils.proxy.get_valid_proxies(domains):
        clash = to_clash(pinfo, meta_or_normal)
        if 'msg' not in clash:
            allp.append(clash)

    return yaml.dump({"proxies": allp}, sort_keys=False)

# def to_clash_yml(proxy):
#     return yaml.dump(to_clash(proxy,'normal'))


def to_clash(proxy, meta_or_normal):

    name = proxy['name']

    if proxy['l3'] in ["kcp", ProxyL3.h3_quic]:
        return {'name': name, 'msg': f"clash does not support {proxy['l3']}", 'type': 'debug'}
    if proxy['transport'] in [ProxyTransport.xhttp, ProxyTransport.httpupgrade]:
        return {'name': name, 'msg': f"clash does not support {proxy['transport']}", 'type': 'debug'}
    # if proxy['proto'] in [Proxy.shado]:

    if meta_or_normal == "normal":
        if proxy.get('flow'):
            return {'name': name, 'msg': "xtls not supported in clash", 'type': 'debug'}
        if proxy['proto'] in [ProxyProto.ssh, ProxyProto.wireguard, ProxyProto.tuic, ProxyProto.hysteria2]:
            return {'name': name, 'msg': f"clash does not support {proxy['proto']}", 'type': 'debug'}
        if proxy['proto'] in ["vless", 'tuic', 'hysteria2']:
            return {'name': name, 'msg': f"{proxy['proto']} not supported in clash", 'type': 'debug'}
        if proxy['transport'] in ["shadowtls", "xhttp"]:
            return {'name': name, 'msg': f"{proxy['transport']} not supported in clash", 'type': 'debug'}
    if proxy['l3'] == ProxyL3.tls_h2 and proxy['proto'] in [ProxyProto.vmess, ProxyProto.vless] and proxy['dbe'].cdn == ProxyCDN.direct:
        return {'name': name, 'msg': "bug tls_h2 vmess and vless in clash meta", 'type': 'warning'}
    base = {}
    # vmess ws
    base["name"] = f"""{proxy['extra_info']} {proxy["name"]} § {proxy['port']} {proxy["dbdomain"].id}"""
    base["type"] = str(proxy["proto"])
    base["server"] = proxy["server"]
    base["port"] = proxy["port"]
    if proxy["proto"] == "ssh":
        base["username"] = proxy["uuid"]
        base["private-key"] = proxy['private_key']
        base["host-key"] = proxy.get('host_keys', [])
        return base
    base["udp"] = True
    if proxy["proto"] == ProxyProto.wireguard:
        base["private-key"] = proxy["wg_pk"]
        base["ip"] = f'{proxy["wg_ipv4"]}/32'
        # base["ipv6"]
        base["public-key"] = proxy["wg_server_pub"]
        base["pre-shared-key"] = proxy["wg_psk"]
        # base["allowed-ips"]
        return base
    if proxy["proto"] == ProxyProto.tuic:
        # base['congestion_control'] = "cubic"
        base['udp-relay-mode'] = 'native'
        base['reduce-rtt'] = True
        base["skip-cert-verify"] = proxy['allow_insecure']
        base['sni'] = proxy['sni']
        # base['heartbeat'] = "10s"
        base['password'] = proxy['uuid']
        base['uuid'] = proxy['uuid']
        return base

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
        base["password"] = proxy["password"]
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
                "password": proxy["shared_secret"],
                "version": 3  # support 1/2/3

            }

        elif proxy["proto"] == "v2ray":
            base["plugin"] = "v2ray-plugin"
            base["type"] = "ss"
            base["plugin-opts"] = {
                "mode": "websocket",
                "tls": "tls" in proxy["l3"],
                "skip-cert-verify": proxy["mode"] == "Fake" or proxy['allow_insecure'],
                "host": proxy['sni'],
                "path": proxy["path"]
            }
        return base
    base['alpn'] = proxy['alpn'].split(',')
    base["skip-cert-verify"] = proxy["mode"] == "Fake"
    if meta_or_normal == "meta" and proxy.get('fingerprint'):
        base['client-fingerprint'] = proxy['fingerprint']

    if proxy["proto"] == "trojan":
        base["password"] = proxy["uuid"]
        base["sni"] = proxy["sni"]
    elif proxy["proto"] == "hysteria2":
        base["password"] = proxy["uuid"]
        base["obfs"] = "salamander"
        base["obfs-password"] = proxy.get('hysteria_obfs_password')
        return base
    else:
        base["uuid"] = proxy["uuid"]
        base["servername"] = proxy["sni"]
        base["tls"] = "tls" in proxy["l3"] or "reality" in proxy["l3"]
    if proxy["proto"] in ["vless", "vmess"]:
        base["packet-encoding"] = "xudp"

    if proxy.get('flow'):
        base["flow"] = proxy['flow']
        # base["flow-show"] = True

    if proxy["proto"] == "vmess":
        base["alterId"] = 0
        base["cipher"] = proxy["cipher"]

    base["network"] = str(proxy["transport"])

    if base["network"] == "ws":
        base["ws-opts"] = {
            "path": proxy["path"]
        }
        if "host" in proxy:
            base["ws-opts"]["headers"] = {"Host": proxy["host"]}

    if base["network"] == "tcp" and proxy['alpn'] != 'h2':
        if proxy['transport'] != ProxyTransport.XTLS:
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
    if proxy['l3'] == ProxyL3.reality:
        base["reality-opts"] = {
            "public-key": proxy['reality_pbk'],
            "short-id": proxy['reality_short_id'],
        }
        if proxy["transport"] != 'grpc':
            base["network"] = 'tcp'

    return base
