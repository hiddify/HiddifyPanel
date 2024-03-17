import datetime
import json
import copy
from flask import render_template, request, g
from hiddifypanel import hutils
from hiddifypanel.models import Proxy, ProxyTransport, ProxyL3, ProxyCDN, ProxyProto, Domain, ConfigEnum, DomainType
from flask_babel import gettext as _
from .xray import is_muxable_agent
OUTBOUND_LEVEL = 8


def configs_as_json(domains: list[Domain], remarks: str) -> str:
    '''Returns xray configs as json'''
    outbounds = []
    for proxy in hutils.proxy.get_valid_proxies(domains):
        outbound = to_xray(proxy)
        if 'msg' not in outbound:
            outbounds.append(outbound)

    outbounds_len = len(outbounds)
    # reutrn no outbound
    if outbounds_len < 1:
        return ''

    all_configs = []
    base_config = json.loads(render_template('base_xray_config.json.j2', remarks=remarks))
    # multiple outbounds needs multiple whole base config not just one with multiple outbounds (at least for v2rayng)
    # https://github.com/2dust/v2rayNG/pull/2827#issue-2127534078
    if outbounds_len > 1:
        for out in outbounds:
            base_config['remarks'] = out['tag']
            base_config['outbounds'].insert(0, out)
            all_configs.append(copy.deepcopy(base_config))
            del base_config['outbounds'][0]
    else:  # single outbound
        base_config['outbounds'].insert(0, outbounds[0])
        all_configs = base_config

    json_configs = json.dumps(all_configs, indent=2, cls=hutils.proxy.ProxyJsonEncoder)
    return json_configs


def to_xray(proxy: dict) -> dict:
    outbound = {
        'tag': f'{proxy["extra_info"]} {proxy["name"]} § {proxy["port"]} {proxy["dbdomain"].id}',
        'protocol': str(proxy['proto']),
        'settings': {},
        'streamSettings': {},
        'mux': {  # default value
            'enabled': False,
            'concurrency': -1
        }
    }
    # add multiplex to outbound
    add_multiplex(outbound, proxy)

    # add stream setting to outbound
    add_stream_settings(outbound, proxy)

    # add protocol settings to outbound
    add_proto_settings(outbound, proxy)

    return outbound

# region proto settings


def add_proto_settings(base: dict, proxy: dict):
    if proxy['proto'] == ProxyProto.wireguard:
        add_wireguard_settings(base, proxy)
    elif proxy['proto'] == ProxyProto.ss:
        add_shadowsocks_settings(base, proxy)
    elif proxy['proto'] == ProxyProto.vless:
        add_vless_settings(base, proxy)
    elif proxy['proto'] == ProxyProto.vmess:
        add_vmess_settings(base, proxy)
    elif proxy['proto'] == ProxyProto.trojan:
        proxy['password'] = proxy['uuid']
        add_trojan_settings(base, proxy)


def add_wireguard_settings(base: dict, proxy: dict):

    base['settings']['secretKey'] = proxy['wg_pk']
    base['settings']['reversed'] = [0, 0, 0]
    base['settings']['mtu'] = 1380  # optional
    base['settings']['peers'] = [{
        'endpoint': f'{proxy["server"]}:{int(proxy["port"])}',
        'publicKey': proxy["wg_server_pub"]
        # 'allowedIPs':'', 'preSharedKey':'', 'keepAlive':'' # optionals
    }]

    # optionals
    # base['settings']['address'] = [f'{proxy["wg_ipv4"]}/32',f'{proxy["wg_ipv6"]}/128']
    # base['settings']['workers'] = 4
    # base['settings']['domainStrategy'] = 'ForceIP' # default


def add_vless_settings(base: dict, proxy: dict):
    base['settings']['vnext'] = [
        {
            'address': proxy['server'],
            'port': proxy['port'],
            "users": [
                {
                    'id': proxy['uuid'],
                    'encryption': 'none',
                    # 'security': 'auto',
                    'flow': 'xtls-rprx-vision' if (proxy['transport'] == ProxyTransport.XTLS or base['streamSettings']['security'] == 'reality') else '',
                    'level': OUTBOUND_LEVEL
                }
            ]
        }
    ]


def add_vmess_settings(base: dict, proxy: dict):
    base['settings']['vnext'] = [
        {
            "address": proxy['server'],
            "port": proxy['port'],
            "users": [
                {
                    "id": proxy['uuid'],
                    "security": proxy['cipher'],
                    "level": OUTBOUND_LEVEL
                }
            ]
        }
    ]


def add_trojan_settings(base: dict, proxy: dict):
    base['settings']['servers'] = [
        {
            # 'email': proxy['uuid'], optional
            'address': proxy['server'],
            'port': proxy['port'],
            'password': proxy['password'],
            'level': OUTBOUND_LEVEL
        }
    ]


def add_shadowsocks_settings(base: dict, proxy: dict):
    base['settings']['servers'] = [
        {
            'address': proxy['server'],
            'port': proxy['port'],
            'method': proxy['cipher'],
            'password': proxy['password'],
            'uot': True,
            'level': OUTBOUND_LEVEL
            # 'email': '', optional
        }
    ]

# endregion


# region stream settings

def add_stream_settings(base: dict, proxy: dict):
    ss = base['streamSettings']
    ss['security'] = 'none'  # default

    # security
    if proxy['l3'] == ProxyL3.reality:
        ss['security'] = 'reality'
    elif proxy['l3'] in [ProxyL3.tls, ProxyL3.tls_h2, ProxyL3.tls_h2_h1]:
        ss['security'] = 'tls'

    # network and transport settings
    if ss['security'] == 'tls' or 'xtls':
        ss['tlsSettings'] = {
            'serverName': proxy['sni'],
            'allowInsecure': proxy['allow_insecure'],
            'fingerprint': proxy['fingerprint'],
            'alpn': [proxy['alpn']],
            # 'minVersion': '1.2',
            # 'disableSystemRoot': '',
            # 'enableSessionResumption': '',
            # 'pinnedPeerCertificateChainSha256': '',
            # 'certificates': '',
            # 'maxVersion': '1.3', # Go lang sets
            # 'cipherSuites': '', # Go lang sets
            # 'rejectUnknownSni': '', # default is false
        }
    if ss['security'] == 'reality':
        ss['network'] = proxy['transport']
        add_reality_stream(ss, proxy)
    if proxy['l3'] == ProxyL3.kcp:
        ss['network'] = 'kcp'
        add_kcp_stream(ss, proxy)

    if proxy['l3'] == ProxyL3.h3_quic:
        add_quic_stream(ss, proxy)

    if proxy['transport'] == 'tcp' or ss['security'] == 'reality' or (ss['security'] == 'none' and proxy['transport'] not in [ProxyTransport.httpupgrade, ProxyTransport.WS]):
        ss['network'] = proxy['transport']
        add_tcp_stream(ss, proxy)
    if proxy['transport'] == ProxyTransport.h2 and ss['security'] == 'none' and ss['security'] != 'reality':
        ss['network'] = proxy['transport']
        add_http_stream(ss, proxy)
    if proxy['transport'] == ProxyTransport.grpc:
        ss['network'] = proxy['transport']
        add_grpc_stream(ss, proxy)
    if proxy['transport'] == ProxyTransport.httpupgrade:
        ss['network'] = proxy['transport']
        add_httpupgrade_stream(ss, proxy)
    if proxy['transport'] == 'ws':
        ss['network'] = proxy['transport']
        add_ws_stream(ss, proxy)

    # tls fragmentaion
    add_tls_fragmentation_stream_settings(base, proxy)


def add_tcp_stream(ss: dict, proxy: dict):
    if proxy['l3'] == ProxyL3.http:
        ss['tcpSettings'] = {
            'header': {
                'type': 'http',
                'request': {
                    'path': [proxy['path']]
                }
            }
            # 'acceptProxyProtocol': False
        }
    else:
        ss['tcpSettings'] = {
            'header': {
                'type': 'none'
            }
            # 'acceptProxyProtocol': False
        }


def add_http_stream(ss: dict, proxy: dict):
    ss['httpSettings'] = {
        'host': proxy['host'],
        'path': proxy['path'],
        # 'read_idle_timeout': 10,  # default disabled
        # 'health_check_timeout': 15,  # default is 15
        # 'method': 'PUT',  # default is 15
        # 'headers': {

        # }
    }


def add_ws_stream(ss: dict, proxy: dict):
    ss['wsSettings'] = {
        'path': proxy['path'],
        'headers': {
            "Host": proxy['host']
        }
        # 'acceptProxyProtocol': False,
    }


def add_grpc_stream(ss: dict, proxy: dict):
    ss['grpcSettings'] = {
        'serviceName': proxy['path'],  # proxy['path'] is equal toproxy['grpc_service_name']
        'idle_timeout': 115,  # by default, the health check is not enabled. may solve some "connection drop" issues
        'health_check_timeout': 20,  # default is 20
        # 'initial_windows_size': 0,  # 0 means disabled. greater than 65535 means Dynamic Window mechanism will be disabled
        # 'permit_without_stream': False, # health check performed when there are no sub-connections
        # 'multiMode': false, # experimental
    }


def add_httpupgrade_stream(ss: dict, proxy: dict):
    ss['httpupgradeSettings'] = {
        'path': proxy['path'],
        'host': proxy['host'],
        # 'acceptProxyProtocol': '', for inbounds only
    }


def add_kcp_stream(ss: dict, proxy: dict):
    # TODO: fix server side configs first
    ss['kcpSettings'] = {}
    return
    ss['kcpSettings'] = {
        'seed': proxy['path'],
        # 'mtu': 1350, # optional, default value is written
        # 'tti': 50, # optional, default value is written
        # 'uplinkCapacity': 5, # optional, default value is written
        # 'downlinkCapacity': 20, # optional, default value is written
        # 'congestion':False, # optional, default value is written
        # 'readBufferSize': 2,# optional, default value is written
        # 'writeBufferSize':2 # optional, default value is written
        # 'header': { # must be same as server (hiddify doesn't use yet)
        #     'type': 'none'  # choices: none(default), srtp, utp, wechat-video, dtls, wireguards
        # }
    }


def add_quic_stream(ss: dict, proxy: dict):
    # TODO: fix server side configs first
    ss['quicSettings'] = {}
    return
    ss['quicSettings'] = {
        'security': 'chacha20-poly1305',
        'key': proxy['path'],
        'header': {
            'type': 'none'
        }
    }


def add_reality_stream(ss: dict, proxy: dict):
    ss['realitySettings'] = {
        'serverName': proxy['sni'],
        'fingerprint': proxy['fingerprint'],
        'shortId': proxy['reality_short_id'],
        'publicKey': proxy['reality_pbk'],
        'show': False,
    }


def add_tls_fragmentation_stream_settings(base: dict, proxy: dict):
    '''Adds tls fragment in the outbounds if tls fragmentation is enabled'''
    if base['streamSettings']['security'] in ['tls', 'reality']:
        if proxy.get('tls_fragment_enable'):
            base['streamSettings']['sockopt'] = {
                'dialerProxy': 'fragment',
                'tcpKeepAliveIdle': 100,
                'tcpNoDelay': True,  # recommended to be enabled with "tcpMptcp": true.
                "mark": 255
                # 'tcpFastOpen': True, # the system default setting be used.
                # 'tcpKeepAliveInterval': 0, # 0 means default GO lang settings, -1 means not enable
                # 'tcpcongestion': bbr, # Not configuring means using the system default value
                # 'tcpMptcp': True, # need to be enabled in both server and client configuration (not supported by panel yet)
            }

# endregion


def add_multiplex(base: dict, proxy: dict):
    if proxy.get('mux_enable') != "xray":
        return

    concurrency = proxy['mux_max_connections']
    if concurrency and concurrency > 0:
        base['mux']['enabled'] = True
        base['mux']['concurrency'] = concurrency
        base['mux']['xudpConcurrency'] = concurrency
        base['mux']['xudpProxyUDP443'] = 'reject'


def add_tls_tricks_to_dict(d: dict, proxy: dict):
    if proxy.get('tls_fragment_enable'):
        if g.user_agent.get('is_shadowrocket'):
            d['fragment'] = f'1,{proxy["tls_fragment_size"]},{proxy["tls_fragment_sleep"]}'
        else:
            d['fragment'] = f'{proxy["tls_fragment_size"]},{proxy["tls_fragment_sleep"]},tlshello'

    if proxy.get("tls_mixed_case"):
        d['mc'] = 1
    if proxy.get("tls_padding_enable"):
        d['padsize'] = proxy["tls_padding_length"]


def add_mux_to_dict(d: dict, proxy):
    if not is_muxable_agent(proxy):
        return

    # according to github.com/hiddify/ray2sing/
    d['muxtype'] = proxy["mux_protocol"]
    d['muxmaxc'] = proxy["mux_max_connections"]
    d['mux'] = proxy['mux_min_streams']
    d['muxsmax'] = proxy["mux_max_streams"]
    d['muxpad'] = proxy["mux_padding_enable"]

    if proxy.get('mux_brutal_enable'):
        d['muxup'] = proxy["mux_brutal_up_mbps"]
        d['muxdown'] = proxy["mux_brutal_down_mbps"]


def add_tls_tricks_to_link(proxy: dict) -> str:
    out = {}
    add_tls_tricks_to_dict(out, proxy)
    return hutils.encode.convert_dict_to_url(out)


def add_mux_to_link(proxy: dict) -> str:
    out = {}
    add_mux_to_dict(out, proxy)
    return hutils.encode.convert_dict_to_url(out)
