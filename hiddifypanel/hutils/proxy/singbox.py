from flask import render_template, request, g
import json

from hiddifypanel import hutils
from hiddifypanel.hutils.proxy.xrayjson import to_xray
from hiddifypanel.models import ProxyProto, ProxyTransport, Domain, ConfigEnum


def configs_as_json(domains: list[Domain], **kwargs) -> str:
    ua = hutils.flask.get_user_agent()
    base_config = json.loads(render_template('base_singbox_config.json.j2'))
    allphttp = [p for p in request.args.get("phttp", "").split(',') if p]
    allptls = [p for p in request.args.get("ptls", "").split(',') if p]

    allp = []
    for d in domains:
        base_config['dns']['rules'][0]['domain'].append(d.domain)
    for pinfo in hutils.proxy.get_valid_proxies(domains):
        sing = to_singbox(pinfo)
        if 'msg' not in sing:
            allp += sing
    base_config['outbounds'] += allp

    select = {
        "type": "selector",
        "tag": "Select",
        "outbounds": [p['tag'] for p in allp if 'shadowtls-out' not in p['tag']],
        "default": "Auto"
    }
    select['outbounds'].insert(0, "Auto")
    base_config['outbounds'].insert(0, select)
    smart = {
        "type": "urltest",
        "tag": "Auto",
        "outbounds": [p['tag'] for p in allp if 'shadowtls-out' not in p],
        "url": "https://www.gstatic.com/generate_204",
        "interval": "10m",
        "tolerance": 200
    }
    base_config['outbounds'].insert(1, smart)
    res = json.dumps(base_config, indent=4, cls=hutils.proxy.ProxyJsonEncoder)
    # if ua['is_hiddify']:
    #     res = res[:-1]+',"experimental": {}}'
    return res


def is_xray_proxy(proxy: dict):
    if g.user_agent.get('is_hiddify_prefere_xray'):
        return True
    if proxy['transport'] == ProxyTransport.xhttp:
        return True
    return False


def to_singbox(proxy: dict) -> list[dict] | dict:
    name = proxy['name']

    all_base = []
    if proxy['l3'] == "kcp":
        return {'name': name, 'msg': "clash does not support kcp", 'type': 'debug'}

    base = {}
    all_base.append(base)
    # vmess ws
    base["tag"] = f"""{proxy['extra_info']} {proxy["name"]} § {proxy['port']} {proxy["dbdomain"].id}"""
    if is_xray_proxy(proxy):
        if hutils.flask.is_client_version(hutils.flask.ClientVersion.hiddify_next, 1, 9, 0):
            base['type'] = "xray"
            xp = to_xray(proxy)
            xp['streamSettings']['sockopt'] = {}
            base['xray_outbound_raw'] = xp
            if proxy.get('tls_fragment_enable'):
                base['xray_fragment'] = {
                    'packets': "tlshello",
                    'length': proxy["tls_fragment_size"],
                    'interval': proxy["tls_fragment_sleep"]
                }
            return all_base
        return {'name': name, 'msg': "xray proxy does not support in this client version", 'type': 'debug'}
    base["type"] = str(proxy["proto"])
    base["server"] = proxy["server"]
    base["server_port"] = int(proxy["port"])
    # base['alpn'] = proxy['alpn'].split(',')
    if proxy["proto"] == "ssr":
        add_ssr(base, proxy)
        return all_base
    if proxy["proto"] == ProxyProto.wireguard:
        add_wireguard(base, proxy)
        return all_base

    if proxy["proto"] in ["ss", "v2ray"]:
        add_shadowsocks_base(all_base, proxy)
        return all_base
    if proxy["proto"] == "ssh":
        add_ssh(all_base, proxy)
        return all_base

    if proxy["proto"] == "trojan":
        base["password"] = proxy["password"]

    if proxy['proto'] in ['vmess', 'vless']:
        base["uuid"] = proxy["uuid"]

    if proxy['proto'] in ['vmess', 'vless', 'trojan']:
        add_multiplex(base, proxy)

    add_tls(base, proxy)

    if g.user_agent.get('is_hiddify'):
        add_tls_tricks(base, proxy)

    if proxy.get('flow'):
        base["flow"] = proxy['flow']
        # base["flow-show"] = True

    if proxy["proto"] == "vmess":
        base["alter_id"] = 0
        base["security"] = proxy["cipher"]

    # base["udp"] = True
    if proxy["proto"] in ["vmess", "vless"]:
        base["packet_encoding"] = "xudp"  # udp packet encoding

    if proxy["proto"] == "tuic":
        add_tuic(base, proxy)
    elif proxy["proto"] == "hysteria2":
        add_hysteria(base, proxy)
    else:
        add_transport(base, proxy)

    return all_base


def add_multiplex(base: dict, proxy: dict):
    if proxy.get('mux_enable') != "singbox":
        return
    base['multiplex'] = {
        "enabled": True,
        "protocol": proxy['mux_protocol'],
        "padding": proxy['mux_padding_enable']
    }
    # Conflicts: max_streams with max_connections and min_streams
    mux_max_streams = proxy.get('mux_max_streams', 0)
    if mux_max_streams and mux_max_streams != 0:
        base['multiplex']['max_streams'] = mux_max_streams
    else:
        base['multiplex']['max_connections'] = proxy.get('mux_max_connections', 0)
        base['multiplex']['min_streams'] = proxy.get('mux_min_streams', 0)

    add_tcp_brutal(base, proxy)


def add_tcp_brutal(base: dict, proxy: dict):
    if 'multiplex' in base:
        if proxy.get('mux_brutal_enable'):
            base['multiplex']['brutal'] = {
                "enabled": proxy.get('mux_brutal_enable', False),
                "up_mbps": proxy.get('mux_brutal_up_mbps', 10),
                "down_mbps": proxy.get('mux_brutal_down_mbps', 10)
            }


def add_udp_over_tcp(base: dict):
    base['udp_over_tcp'] = {
        "enabled": True,
        "version": 2
    }


def add_tls(base: dict, proxy: dict):
    if not ("tls" in proxy["l3"] or "reality" in proxy["l3"]):
        return
    base["tls"] = {
        "enabled": True,
        "server_name": proxy["sni"]
    }
    if proxy['proto'] not in ["tuic", "hysteria2"]:
        base["tls"]["utls"] = {
            "enabled": True,
            "fingerprint": proxy.get('fingerprint', 'none')
        }

    if "reality" in proxy["l3"]:
        base["tls"]["reality"] = {
            "enabled": True,
            "public_key": proxy['reality_pbk'],
            "short_id": proxy['reality_short_id']
        }
    base["tls"]['insecure'] = proxy['allow_insecure'] or (proxy["mode"] == "Fake")
    base["tls"]["alpn"] = proxy['alpn'].split(',')
    # base['ech'] = {
    #     "enabled": True,
    # }


def add_tls_tricks(base: dict, proxy: dict):
    if proxy.get('tls_fragment_enable'):
        base['tls_fragment'] = {
            'enabled': True,
            'size': proxy["tls_fragment_size"],
            'sleep': proxy["tls_fragment_sleep"]
        }

    if 'tls' in base:
        if proxy.get("tls_padding_enable") or proxy.get("tls_mixed_case"):
            base['tls']['tls_tricks'] = {}
        if proxy.get("tls_padding_enable"):
            base['tls']['tls_tricks']['padding_size'] = proxy["tls_padding_length"]

        if proxy.get("tls_mixed_case"):
            base['tls']['tls_tricks']['mixedcase_sni'] = True


def add_transport(base: dict, proxy: dict):
    if proxy['l3'] == 'reality' and proxy['transport'] not in ["grpc"]:
        return
    base["transport"] = {}
    if proxy['transport'] in ["ws", "WS"]:
        base["transport"] = {
            "type": "ws",
            "path": proxy["path"],
            "early_data_header_name": "Sec-WebSocket-Protocol"
        }
        if "host" in proxy:
            base["transport"]["headers"] = {"Host": proxy["host"]}

    if proxy['transport'] in [ProxyTransport.httpupgrade]:
        base["transport"] = {
            "type": "httpupgrade",
            "path": proxy["path"]
        }
        if "host" in proxy:
            base["transport"]["headers"] = {"Host": proxy["host"]}

    if proxy["transport"] in ["tcp", "h2"]:
        base["transport"] = {
            "type": "http",
            "path": proxy.get("path", ""),
            "idle_timeout": "15s",
            "ping_timeout": "15s"
            # "method": "",
            # "headers": {},
        }

        if 'host' in proxy:
            base["transport"]["host"] = [proxy["host"]]

    if proxy["transport"] == "grpc":
        base["transport"] = {
            "type": "grpc",
            "service_name": proxy["grpc_service_name"],
            "idle_timeout": "115s",
            "ping_timeout": "15s",
            # "permit_without_stream": false
        }


def add_ssr(base: dict, proxy: dict):

    base["method"] = proxy["cipher"]
    base["password"] = proxy["uuid"]
    # base["udp"] = True
    base["obfs"] = proxy["ssr-obfs"]
    base["protocol"] = proxy["ssr-protocol"]
    base["protocol-param"] = proxy["fakedomain"]


def add_wireguard(base: dict, proxy: dict):

    base["local_address"] = f'{proxy["wg_ipv4"]}/32'
    base["private_key"] = proxy["wg_pk"]
    base["peer_public_key"] = proxy["wg_server_pub"]

    base["pre_shared_key"] = proxy["wg_psk"]

    base["mtu"] = 1380
    if g.user_agent.get('is_hiddify') and hutils.flask.is_client_version(hutils.flask.ClientVersion.hiddify_next, 0, 15, 0):
        base["fake_packets"] = proxy["wg_noise_trick"]


def add_shadowsocks_base(all_base: list[dict], proxy: dict):
    base = all_base[0]
    base["type"] = "shadowsocks"
    base["method"] = proxy["cipher"]
    base["password"] = proxy["password"]
    add_udp_over_tcp(base)
    add_multiplex(base, proxy)
    if proxy["transport"] == "faketls":
        base["plugin"] = "obfs-local"
        base["plugin_opts"] = f'obfs=tls;obfs-host={proxy["fakedomain"]}'
    if proxy['proto'] == 'v2ray':
        base["plugin"] = "v2ray-plugin"
        # "skip-cert-verify": proxy["mode"] == "Fake" or proxy['allow_insecure'],
        base["plugin_opts"] = f'mode=websocket;path={proxy["path"]};host={proxy["host"]};tls'

    if proxy["transport"] == "shadowtls":
        base['detour'] = base['tag'] + "_shadowtls-out §hide§"

        shadowtls_base = {
            "type": "shadowtls",
            "tag": base['detour'],
            "server": base['server'],
            "server_port": base['server_port'],
            "version": 3,
            "password": proxy["shared_secret"],
            "tls": {
                "enabled": True,
                "server_name": proxy["fakedomain"],
                "utls": {
                    "enabled": True,
                    "fingerprint": proxy.get('fingerprint', 'none')
                },
                # "alpn": proxy['alpn'].split(',')
            }
        }
        # add_utls(shadowtls_base)
        del base['server']
        del base['server_port']
        all_base.append(shadowtls_base)


def add_ssh(all_base: list[dict], proxy: dict):
    base = all_base[0]
    # base["client_version"]= "{{ssh_client_version}}"
    base["user"] = proxy['uuid']
    base["private_key"] = proxy['private_key']  # .replace('\n', '\\n')

    base["host_key"] = proxy.get('host_keys', [])

    socks_front = {
        "type": "socks",
        "tag": base['tag'] + "+UDP",
        "server": "127.0.0.1",
        "server_port": 2000,
        "version": "5",
        "udp_over_tcp": True,
        "network": "tcp",
        "detour": base['tag']
    }
    all_base.append(socks_front)


def add_tuic(base: dict, proxy: dict):
    base['congestion_control'] = "cubic"
    base['udp_relay_mode'] = 'native'
    base['zero_rtt_handshake'] = True
    base['heartbeat'] = "10s"
    base['password'] = proxy['uuid']
    base['uuid'] = proxy['uuid']


def add_hysteria(base: dict, proxy: dict):
    base['up_mbps'] = proxy.get(ConfigEnum.hysteria_up_mbps)
    base['down_mbps'] = proxy.get(ConfigEnum.hysteria_down_mbps)
    # TODO: check the obfs should be empty or not exists at all
    if proxy.get('hysteria_obfs_enable'):
        base['obfs'] = {
            "type": "salamander",
            "password": proxy.get('hysteria_obfs_password')
        }
    base['password'] = proxy['uuid']
