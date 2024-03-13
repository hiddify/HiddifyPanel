from flask import current_app
import glob
import json
from ipaddress import IPv4Address, IPv6Address
from hiddifypanel.models import Proxy, ProxyProto, ProxyTransport, ProxyCDN, Domain, DomainType, ConfigEnum


def get_ssh_hostkeys(dojson=False) -> list[str] | str:
    key_files = glob.glob(current_app.config['HIDDIFY_CONFIG_PATH'] + "/other/ssh/host_key/*_key.pub")
    host_keys = []
    for file_name in key_files:
        with open(file_name, "r") as f:
            host_key = f.read().strip()
            host_key = host_key.split()
            if len(host_key) > 2:
                host_key = host_key[:2]  # strip the hostname part
            host_key = " ".join(host_key)
            host_keys.append(host_key)
    if dojson:
        return json.dumps(host_keys)
    return host_keys


def is_proxy_valid(proxy: Proxy, domain_db: Domain, port: int) -> dict | None:
    name = proxy.name
    l3 = proxy.l3
    if not port:
        return {'name': name, 'msg': "port not defined", 'type': 'error', 'proto': proxy.proto}
    if "reality" not in l3 and domain_db.mode == DomainType.reality:
        return {'name': name, 'msg': "reality proxy not in reality domain", 'type': 'debug', 'proto': proxy.proto}

    if "reality" in l3 and domain_db.mode != DomainType.reality:
        return {'name': name, 'msg': "reality proxy not in reality domain", 'type': 'debug', 'proto': proxy.proto}

    if "reality" in l3 and domain_db.grpc and ProxyTransport.grpc != proxy.transport:
        return {'name': name, 'msg': "reality proxy not in reality domain", 'type': 'debug', 'proto': proxy.proto}

    if "reality" in l3 and (not domain_db.grpc) and ProxyTransport.grpc == proxy.transport:
        return {'name': name, 'msg': "reality proxy not in reality domain", 'type': 'debug', 'proto': proxy.proto}

    is_cdn = ProxyCDN.CDN == proxy.cdn or ProxyCDN.Fake == proxy.cdn
    if is_cdn and domain_db.mode not in [DomainType.cdn, DomainType.auto_cdn_ip, DomainType.worker]:
        # print("cdn proxy not in cdn domain", domain, name)
        return {'name': name, 'msg': "cdn proxy not in cdn domain", 'type': 'debug', 'proto': proxy.proto}

    if not is_cdn and domain_db.mode in [DomainType.cdn, DomainType.auto_cdn_ip, DomainType.worker]:
        # print("not cdn proxy  in cdn domain", domain, name, proxy.cdn)
        return {'name': name, 'msg': "not cdn proxy  in cdn domain", 'type': 'debug', 'proto': proxy.proto}

    if proxy.cdn == ProxyCDN.relay and domain_db.mode not in [DomainType.relay]:
        return {'name': name, 'msg': "relay proxy not in relay domain", 'type': 'debug', 'proto': proxy.proto}

    if proxy.cdn != ProxyCDN.relay and domain_db.mode in [DomainType.relay]:
        return {'name': name, 'msg': "relay proxy not in relay domain", 'type': 'debug', 'proto': proxy.proto}

    if domain_db.mode == DomainType.worker and proxy.transport == ProxyTransport.grpc:
        return {'name': name, 'msg': "worker does not support grpc", 'type': 'debug', 'proto': proxy.proto}

    if domain_db.mode != DomainType.old_xtls_direct and "tls" in proxy.l3 and proxy.cdn == ProxyCDN.direct and proxy.transport in [ProxyTransport.tcp, ProxyTransport.XTLS]:
        return {'name': name, 'msg': "only  old_xtls_direct  support this", 'type': 'debug', 'proto': proxy.proto}

    if proxy.proto == "trojan" and not is_tls(l3):
        return {'name': name, 'msg': "trojan but not tls", 'type': 'warning', 'proto': proxy.proto}

    if l3 == "http" and ProxyTransport.XTLS in proxy.transport:
        return {'name': name, 'msg': "http and xtls???", 'type': 'warning', 'proto': proxy.proto}

    if l3 == "http" and proxy.proto in [ProxyProto.ss, ProxyProto.ssr]:
        return {'name': name, 'msg': "http and ss or ssr???", 'type': 'warning', 'proto': proxy.proto}


def get_port(proxy: Proxy, hconfigs: dict, domain_db: Domain, ptls: int, phttp: int, pport: int | None) -> int:
    l3 = proxy.l3
    port = 443
    if isinstance(phttp, str):
        phttp = int(phttp) if phttp != "None" else None  # type: ignore
    if isinstance(ptls, str):
        ptls = int(ptls) if ptls != "None" else None  # type: ignore
    if l3 == "kcp":
        port = hconfigs[ConfigEnum.kcp_ports].split(",")[0]
    elif proxy.proto == ProxyProto.wireguard:
        port = hconfigs[ConfigEnum.wireguard_port]
    elif proxy.proto == "tuic":
        port = domain_db.internal_port_tuic
    elif proxy.proto == "hysteria2":
        port = domain_db.internal_port_hysteria2
    elif l3 == 'ssh':
        port = hconfigs[ConfigEnum.ssh_server_port]
    elif is_tls(l3):
        port = ptls
    elif l3 == "http":
        port = phttp
    else:
        port = int(pport)  # type: ignore
    return port


def is_tls(l3) -> bool:
    return 'tls' in l3 or "reality" in l3


class ProxyJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, IPv4Address) or isinstance(obj, IPv6Address):
            return str(obj)
        return super().default(obj)
