import json
import copy
from flask import render_template, g
from hiddifypanel import hutils
from hiddifypanel.models import ProxyTransport, ProxyL3, ProxyProto, Domain, User
from flask_babel import gettext as _
from hiddifypanel.models import hconfig, ConfigEnum
from .xray import is_muxable_agent, OUTBOUND_LEVEL


def configs_as_json(domains: list[Domain], user: User, expire_days: int, remarks: str) -> str:
    '''Returns xray configs as json'''
    all_configs = []

    # region show usage
    if hconfig(ConfigEnum.show_usage_in_sublink) and not g.user_agent.get('is_hiddify'):
        # determine usages
        tag = '⏳ ' if user.is_active else '✖ '
        if user.usage_limit_GB < 1000:
            tag += f'{round(user.current_usage_GB,3)}/{str(user.usage_limit_GB).replace(".0","")}GB'
        elif user.usage_limit_GB < 100000:
            tag += f'{round(user.current_usage_GB/1000,3)}/{str(round(user.usage_limit_GB/1000,1)).replace(".0","")}TB'
        else:
            tag += '#No Usage Limit'
        tag += ' 📅 '
        if expire_days < 1000:
            tag += _(f'%(expire_days)s days', expire_days=expire_days)
        else:
            tag += '#No Time Limit'
        tag = tag.strip()

        # add usage as a config
        all_configs.append(
            null_config(tag)
        )
    # endregion

    if not user.is_active:
        # region show status (active/disable)
        tag = '✖ ' + (hutils.encode.url_encode('بسته شما به پایان رسید') if hconfig(ConfigEnum.lang) == 'fa' else 'Package Ended')
        # add user status
        all_configs.append(
            null_config(tag)
        )
        # endregion
    else:
        # TODO: seperate codes to small functions
        # TODO: check what are unsupported protocols in other apps
        unsupported_protos = {}
        unsupported_transport = {}
        if g.user_agent.get('is_v2rayng'):
            # TODO: ensure which protocols are not supported in v2rayng
            unsupported_protos = {ProxyProto.wireguard, ProxyProto.hysteria, ProxyProto.hysteria2,
                                  ProxyProto.tuic, ProxyProto.ss, ProxyProto.ssr, ProxyProto.ssh}
            if not hutils.flask.is_client_version(hutils.flask.ClientVersion.v2ryang, 1, 8, 18):
                unsupported_transport = {ProxyTransport.httpupgrade}

        # multiple outbounds needs multiple whole base config not just one with multiple outbounds (at least for v2rayng)
        # https://github.com/2dust/v2rayNG/pull/2827#issue-2127534078
        outbounds = []
        for proxy in hutils.proxy.get_valid_proxies(domains):
            if proxy['proto'] in unsupported_protos:
                continue
            if proxy['transport'] in unsupported_transport:
                continue
            outbound = to_xray(proxy)
            outbounds.append(outbound)

        base_config = json.loads(render_template('base_xray_config.json.j2', remarks=remarks))
        if len(outbounds) > 1:
            for out in outbounds:
                base = copy.deepcopy(base_config)
                base['remarks'] = out['tag']
                base['outbounds'].insert(0, out)
                # if all_configs:
                #     all_configs.insert(0, copy.deepcopy(base_config))
                # else:
                all_configs.append(base)

        else:  # single outbound
            base_config['outbounds'].insert(0, outbounds[0])
            all_configs = base_config

    if not all_configs:
        return ''

    json_configs = json.dumps(all_configs, indent=2, cls=hutils.proxy.ProxyJsonEncoder)
    return json_configs


def to_xray(proxy: dict) -> dict:
    outbound = {
        'tag': f'{proxy["extra_info"]} {proxy["name"]}',
        'protocol': str(proxy['proto']),
        'settings': {},
        'streamSettings': {},
        # 'mux': {  # default value
        #     # 'enabled': False,
        #     # 'concurrency': -1
        # }
    }
    outbound['protocol'] = 'shadowsocks' if outbound['protocol'] == 'ss' else outbound['protocol']
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
    elif proxy['l3'] in [ProxyL3.tls, ProxyL3.tls_h2, ProxyL3.tls_h2_h1, ProxyL3.h3_quic]:
        ss['security'] = 'tls'

    # network and transport settings
    # THE CURRENT CODE WORKS BUT THE CORRECT CONDITINO SHOULD BE THIS:
    # ss['security'] == 'tls' or 'xtls' -----> ss['security'] in ['tls','xtls']
    # TODO: FIX THE CONDITION AND TEST CONFIGS ON THE CLIENT SIDE
    if ss['security'] == 'reality':
        ss['network'] = proxy['transport']
        add_reality_stream(ss, proxy)
    elif ss['security'] in ['tls', "xtls"] and proxy['proto'] != ProxyProto.ss:

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

    if proxy['l3'] == ProxyL3.kcp:
        ss['network'] = 'kcp'
        add_kcp_stream(ss, proxy)

    if proxy['l3'] == ProxyL3.h3_quic:
        add_quic_stream(ss, proxy)

    if (proxy['transport'] == 'tcp' and ss['security'] != 'reality') or (ss['security'] == 'none' and proxy['transport'] not in [ProxyTransport.httpupgrade, ProxyTransport.WS] and proxy['proto'] != ProxyProto.ss):
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
    if proxy['transport'] == ProxyTransport.splithttp:
        ss['network'] = proxy['transport']
        add_splithttp_stream(ss, proxy)
    if proxy['transport'] == 'ws':
        ss['network'] = proxy['transport']
        add_ws_stream(ss, proxy)

    if proxy['proto'] == ProxyProto.ss:
        ss['network'] = 'tcp'

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


def add_splithttp_stream(ss: dict, proxy: dict):
    ss['splithttpSettings'] = {
        'path': proxy['path'],
        'host': proxy['host'],
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        }
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
    if proxy.get('mux_enable') != "xray" or not is_muxable_agent(proxy):
        return

    concurrency = proxy['mux_max_connections']
    if concurrency and concurrency > 0:
        base['mux'] = {'enabled': True,
                       'concurrency': concurrency,
                       'xudpConcurrency': concurrency,
                       'xudpProxyUDP443': 'reject',
                       }


def null_config(tag: str) -> dict:
    base_config = json.loads(render_template('base_xray_config.json.j2', remarks=tag))
    base_config['outbounds'][0]["protocol"] = "blackhole"
    return base_config
