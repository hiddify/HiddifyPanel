import datetime
import json
from flask import render_template, request, g
from hiddifypanel import hutils
from hiddifypanel.models import Proxy, ProxyTransport, ProxyL3, ProxyCDN, ProxyProto, Domain, hconfig, ConfigEnum, DomainType
from flask_babel import gettext as _

OUTBOUND_LEVEL = 8


def to_link(proxy: dict) -> str | dict:
    if 'error' in proxy:
        return proxy

    orig_name_link = (proxy['extra_info'] + " " + proxy["name"]).strip()
    name_link = hutils.encode.url_encode(orig_name_link)
    if proxy['proto'] == 'vmess':
        # print(proxy)
        vmess_type = None
        if proxy["transport"] == 'tcp':
            vmess_type = 'http'
        if 'grpc_mode' in proxy:
            vmess_type = proxy['grpc_mode']
        vmess_data = {"v": "2",
                      "ps": orig_name_link,
                      "add": proxy['server'],
                      "port": proxy['port'],
                      "id": proxy["uuid"],
                      "aid": 0,
                      "scy": proxy['cipher'],
                      "net": proxy["transport"],
                      "type": vmess_type or "none",
                      "host": proxy.get("host", ""),
                      "alpn": proxy.get("alpn", "h2,http/1.1"),
                      "path": proxy["path"] if "path" in proxy else "",
                      "tls": "tls" if "tls" in proxy["l3"] else "",
                      "sni": proxy["sni"],
                      "fp": proxy["fingerprint"]
                      }
        if 'reality' in proxy["l3"]:
            vmess_data['tls'] = "reality"
            vmess_data['pbk'] = proxy['reality_pbk']
            vmess_data['sid'] = proxy['reality_short_id']

        add_tls_tricks_to_dict(vmess_data, proxy)
        add_mux_to_dict(vmess_data, proxy)

        return "vmess://" + hutils.encode.do_base_64(f'{json.dumps(vmess_data,cls=hutils.proxy.ProxyJsonEncoder)}')
    if proxy['proto'] == 'ssh':
        baseurl = 'ssh://'
        if g.user_agent.get('is_streisand'):
            streisand_ssh = hutils.encode.do_base_64(f'{proxy["uuid"]}:0:{proxy["private_key"]}::@{proxy["server"]}:{proxy["port"]}')
            baseurl += f'{streisand_ssh}#{name_link}'
        else:
            hk = ",".join(proxy["host_key"])
            pk = proxy["private_key"].replace('\n', '')
            baseurl += f'{proxy["uuid"]}@{proxy["server"]}:{proxy["port"]}/?file=ssh&pk={pk}&hk={hk}#{name_link}'

        return baseurl
    if proxy['proto'] == "ssr":
        baseurl = f'ssr://{proxy["cipher"]}:{proxy["uuid"]}@{proxy["server"]}:{proxy["port"]}'
        return baseurl
    if proxy['proto'] in ['ss', 'v2ray']:
        baseurl = f'ss://{proxy["cipher"]}:{proxy["password"]}@{proxy["server"]}:{proxy["port"]}'
        if proxy['mode'] == 'faketls':
            return f'{baseurl}?plugin=obfs-local%3Bobfs%3Dtls%3Bobfs-host%3D{proxy["fakedomain"]}%3Budp-over-tcp=true#{name_link}'
        # if proxy['mode'] == 'shadowtls':
        #     return f'{baseurl}?plugin=shadow-tls%3Bpassword%3D{proxy["proxy_path"]}%3Bhost%3D{proxy["fakedomain"]}%3Budp-over-tcp=true#{name_link}'
        if proxy['proto'] == 'v2ray':
            return f'{baseurl}?plugin=v2ray-plugin%3Bmode%3Dwebsocket%3Bpath%3D{proxy["path"]}%3Bhost%3D{proxy["host"]}%3Btls%3Budp-over-tcp=true#{name_link}'
        if proxy['transport'] == 'shadowsocks':
            return baseurl
    if proxy['proto'] == 'tuic':
        baseurl = f'tuic://{proxy["uuid"]}:{proxy["uuid"]}@{proxy["server"]}:{proxy["port"]}?congestion_control=cubic&udp_relay_mode=native&sni={proxy["sni"]}&alpn=h3'
        if proxy['mode'] == 'Fake' or proxy['allow_insecure']:
            baseurl += "&allow_insecure=1"
        return f"{baseurl}#{name_link}"
    if proxy['proto'] == 'hysteria2':
        baseurl = f'hysteria2://{proxy["uuid"]}@{proxy["server"]}:{proxy["port"]}?hiddify=1&obfs=salamander&obfs-password={hconfig(ConfigEnum.proxy_path)}&sni={proxy["sni"]}'
        if proxy['mode'] == 'Fake' or proxy['allow_insecure']:
            baseurl += "&insecure=1"
        return f"{baseurl}#{name_link}"
    if proxy['proto'] == ProxyProto.wireguard:
        if g.user_agent.get('is_streisand'):
            return f'wireguard://{proxy["server"]}:{proxy["port"]}?private_key={proxy["wg_pk"]}&peer_public_key={proxy["wg_server_pub"]}&pre_shared_key={proxy["wg_psk"]}&reserved=0,0,0#{name_link}'
        else:
            # hiddify_format =
            # f'wg://{proxy["server"]}:{proxy["port"]}/?pk={proxy["wg_pk"]}&local_address={proxy["wg_ipv4"]}/32&peer_pk={proxy["wg_server_pub"]}&pre_shared_key={proxy["wg_psk"]}&workers=4&mtu=1380&reserved=0,0,0&ifp={proxy["wg_noise_trick"]}#{name_link}'
            return f'wg://{proxy["server"]}:{proxy["port"]}?publicKey={proxy["wg_pub"]}&privateKey={proxy["wg_pk"]}=&presharedKey={proxy["wg_psk"]}&ip=10.0.0.1&mtu=1380&keepalive=30&udp=1&reserved=0,0,0&ifp={proxy["wg_noise_trick"]}#{name_link}'

    baseurl = f'{proxy["proto"]}://{proxy["uuid"]}@{proxy["server"]}:{proxy["port"]}?hiddify=1'
    baseurl += f'&sni={proxy["sni"]}&type={proxy["transport"]}'
    baseurl += f"&alpn={proxy['alpn']}"

    # the ray2sing supports vless, vmess and trojan tls tricks and mux
    # the vmess handled already

    baseurl += add_mux_to_link(proxy)
    baseurl += add_tls_tricks_to_link(proxy)

    # infos+=f'&alpn={proxy["alpn"]}'
    baseurl += f'&path={proxy["path"]}' if "path" in proxy else ""
    baseurl += f'&host={proxy["host"]}' if "host" in proxy else ""
    if "grpc" == proxy["transport"]:
        baseurl += f'&serviceName={proxy["grpc_service_name"]}&mode={proxy["grpc_mode"]}'
    # print(proxy['cdn'],proxy["transport"])
    if request.args.get("fragment"):
        baseurl += f'&fragment=' + request.args.get("fragment")  # type: ignore
    if "ws" == proxy["transport"] and proxy['cdn'] and request.args.get("fragment_v1"):
        baseurl += f'&fragment_v1=' + request.args.get("fragment_v1")  # type: ignore
    if 'vless' == proxy['proto']:
        baseurl += "&encryption=none"
    if proxy.get('fingerprint', 'none') != 'none':
        baseurl += "&fp=" + proxy['fingerprint']
    if proxy['l3'] != 'quic':
        if proxy.get('l3') != ProxyL3.reality and (proxy.get('transport') == ProxyTransport.tcp or proxy.get('transport') == ProxyTransport.httpupgrade) and proxy['proto'] in [ProxyProto.vless, ProxyProto.trojan]:
            baseurl += '&headerType=http'
        else:
            baseurl += '&headerType=None'
    if proxy['mode'] == 'Fake' or proxy['allow_insecure']:
        baseurl += "&allowInsecure=true"
    if proxy.get('flow'):
        baseurl += f'&flow={proxy["flow"]}'

    infos = f'#{name_link}'

    if 'reality' in proxy["l3"]:
        return f"{baseurl}&security=reality&pbk={proxy['reality_pbk']}&sid={proxy['reality_short_id']}{infos}"
    if 'tls' in proxy['l3']:
        return f'{baseurl}&security=tls{infos}'
    if proxy['l3'] == 'http':
        return f'{baseurl}&security=none{infos}'
    return proxy


def make_v2ray_configs(user, user_activate, domains: list[Domain], expire_days, ip_debug, db_domain, has_auto_cdn, asn, profile_title, **kwargs) -> str:
    res = []

    ua = hutils.flask.get_user_agent()
    if hconfig(ConfigEnum.show_usage_in_sublink):

        if not ua['is_hiddify']:

            fake_ip_for_sub_link = datetime.datetime.now().strftime(f"%H.%M--%Y.%m.%d.time:%H%M")
            # if ua['app'] == "Fair1":
            #     res.append(f'trojan://1@{fake_ip_for_sub_link}?sni=fake_ip_for_sub_link&security=tls#{round(user.current_usage_GB,3)}/{user.usage_limit_GB}GB_Remain:{expire_days}days')
            # else:

            # res.append(f'trojan://1@{fake_ip_for_sub_link}?sni=fake_ip_for_sub_link&security=tls#{hutils.encode.url_encode(profile_title)}')

            name = '⏳' if user_activate else '✖'
            if user.usage_limit_GB < 1000:
                name += f'{round(user.current_usage_GB,3)}/{str(user.usage_limit_GB).replace(".0","")}GB'
            elif user.usage_limit_GB < 100000:
                name += f'{round(user.current_usage_GB/1000,3)}/{str(round(user.usage_limit_GB/1000,1)).replace(".0","")}TB'
            else:
                res.append("#No Usage Limit")
            if expire_days < 1000:
                name += " " + _(f'📅%(expire_days)s days', expire_days=expire_days)
            else:
                res.append("#No Time Limit")

            name = name.strip()
            if len(name) > 3:
                res.append(f'trojan://1@{fake_ip_for_sub_link}?sni=fake_ip_for_sub_link&security=tls#{hutils.encode.url_encode(name)}')

    if ua['is_browser']:
        res.append(f'#Hiddify auto ip: {ip_debug}')

    if not user_activate:

        if hconfig(ConfigEnum.lang) == 'fa':
            res.append('trojan://1@1.1.1.1#' + hutils.encode.url_encode('✖بسته شما به پایان رسید'))
        else:
            res.append('trojan://1@1.1.1.1#' + hutils.encode.url_encode('✖Package_Ended'))
        return "\n".join(res)

    for pinfo in hutils.proxy.get_valid_proxies(domains):
        link = to_link(pinfo)
        if 'msg' not in link:
            res.append(link)
    return "\n".join(res)


def configs_as_json(domains: list[Domain], remarks: str) -> str:
    '''Returns xray configs as json'''
    base_config = json.loads(render_template('base_xray_config.json.j2', remarks=remarks))

    for proxy in hutils.proxy.get_valid_proxies(domains):
        outbound = to_xray(proxy)
        if 'msg' not in outbound:
            base_config['outbounds'].insert(0, outbound)

    json_configs = json.dumps(base_config, indent=4, cls=hutils.proxy.ProxyJsonEncoder)
    return json_configs


def to_xray(proxy: dict) -> list[dict] | dict:
    all_base = []
    base = {
        'tag': f'{proxy["extra_info"]} {proxy["name"]} § {proxy["port"]} {proxy["dbdomain"].id}',
        'protocol': str(proxy['proto']),
        'settings': {},
        'streamSettings': {},
        'mux': {  # default value
            'enabled': False,
            'concurrency': -1
        }
    }
    all_base.append(base)

    add_xray_multiplex(base)

    add_xray_settings(base, proxy)

    add_xray_stream_settings(base, proxy)

    return all_base


def add_xray_settings(base: dict, proxy: dict):
    if proxy['proto'] == ProxyProto.wireguard:
        add_xray_wireguard(base, proxy)
    elif proxy['proto'] == ProxyProto.ss:
        add_xray_shadowsocks(base, proxy)
    elif proxy['proto'] == ProxyProto.vless:
        add_xray_vless(base, proxy)
    elif proxy['proto'] == ProxyProto.vmess:
        add_xray_vmess(base, proxy)
    elif proxy['proto'] == ProxyProto.trojan:
        proxy['password'] = proxy['uuid']
        add_xray_trojan(base, proxy)


def add_xray_wireguard(base: dict, proxy: dict):

    base['settings']['secretKey'] = proxy['wg_pk']
    base['settings']['reversed'] = [0, 0, 0]
    base['settings']['mtu'] = 1380  # optional
    base['settings']['peers'] = [{
        # 'allowedIPs':'', 'preSharedKey':'', 'keepAlive':'' # optionals
        'endpoint': f'{proxy["server"]}:{int(proxy["port"])}',
        'publicKey': proxy["wg_server_pub"]
    }]

    # optionals
    # base['settings']['address'] = [f'{proxy["wg_ipv4"]}/32',f'{proxy["wg_ipv6"]}/128']
    # base['settings']['workers'] = 4
    # base['settings']['domainStrategy'] = 'ForceIP' # default


def add_xray_vless(base: dict, proxy: dict):
    base['settings']['vnext'] = [
        {
            'address': proxy['server'],
            'port': proxy['port'],
            "users": [
                {
                    'id': proxy['uuid'],
                    'encryption': 'none',
                    # 'security': 'auto',
                    'flow': 'xtls-rprx-vision' if proxy['transport'] == ProxyTransport.XTLS else '',
                    'level': OUTBOUND_LEVEL
                }
            ]
        }
    ]


def add_xray_vmess(base: dict, proxy: dict):
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


def add_xray_trojan(base: dict, proxy: dict):
    base['settings']['servers'] = [
        {
            # 'email': proxy['uuid'], optional
            'address': proxy['server'],
            'port': proxy['port'],
            'password': proxy['password'],
            'level': OUTBOUND_LEVEL
        }
    ]


def add_xray_shadowsocks(base: dict, proxy: dict):
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


def add_xray_stream_settings(base: dict, proxy: dict):
    ss = base['streamSettings']
    ss['security'] = 'none'  # default
    # security
    if proxy['l3'] == ProxyL3.reality:
        ss['security'] = 'xtls'
    elif proxy['l3'] in [ProxyL3.tls, ProxyL3.tls_h2, ProxyL3.tls_h2_h1]:
        ss['security'] = 'tls'

    # network and transport settings
    if ss['security'] == 'tls' or 'xtls':
        ss['tlsSettings'] = {
            'serverName': proxy['sni'],
            'allowInsecure': proxy['allow_insecure'],
            'fingerprint': proxy['fingerprint'],
            'alpn': proxy['alpn'],
            # 'minVersion': '1.2',
            # 'disableSystemRoot': '',
            # 'enableSessionResumption': '',
            # 'pinnedPeerCertificateChainSha256': '',
            # 'certificates': '',
            # 'maxVersion': '1.3', # Go lang sets
            # 'cipherSuites': '', # Go lang sets
            # 'rejectUnknownSni': '', # default is false
        }

    if proxy['transport'] == ProxyTransport.tcp:
        ss['network'] = proxy['transport']
        ss['tcpSettings'] = {
            'header': {
                'type': 'none'
            }
            # 'acceptProxyProtocol': False
        }
    elif proxy['transport'] == ProxyTransport.h2:
        ss['network'] = proxy['transport']

    elif proxy['transport'] == ProxyTransport.grpc:
        ss['network'] = proxy['transport']
        ss['grpcSettings'] = {
            'serviceName': proxy['path'],  # proxy['path'] is equal toproxy['grpc_service_name']
            'idle_timeout': 115,  # by default, the health check is not enabled. may solve some "connection drop" issues
            'health_check_timeout': 20,  # default is 20
            # 'initial_windows_size': 0,  # 0 means disabled. greater than 65535 means Dynamic Window mechanism will be disabled
            # 'permit_without_stream': False, # health check performed when there are no sub-connections
            # 'multiMode': false, # experimental
        }
    elif proxy['transport'] == ProxyTransport.httpupgrade:
        ss['network'] = proxy['transport']
        ss['httpupgradeSettings'] = {
            'path': proxy['path'],
            'host': proxy['host'],
            # 'acceptProxyProtocol': '', for inbounds only
        }
    elif proxy['transport'] == ProxyTransport.WS:
        ss['network'] = proxy['transport']
        ss['wsSettings'] = {
            'path': proxy['path'],
            'headers': {
                "Host": proxy['host']
            }
            # 'acceptProxyProtocol': False,
        }

    # tls fragmentaion
    add_xray_tls_fragmentation(base)


def add_xray_tls_fragmentation(base: dict):
    '''Adds tls fragment in the outbounds if tls fragmentation is enabled'''
    if base['streamSettings']['security'] in ['tls', 'xtls']:
        if hconfig(ConfigEnum.tls_fragment_enable):
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


def add_xray_multiplex(base: dict):
    if hconfig(ConfigEnum.mux_enable):
        concurrency = hutils.convert.to_int(hconfig(ConfigEnum.mux_max_connections))
        if concurrency and concurrency > 0:
            base['mux']['enabled'] = True
            base['mux']['concurrency'] = concurrency
            base['mux']['xudpConcurrency'] = concurrency
            base['mux']['xudpProxyUDP443'] = 'reject'


def add_tls_tricks_to_link(proxy: dict) -> str:
    out = {}
    add_tls_tricks_to_dict(out, proxy)
    return hutils.encode.convert_dict_to_url(out)


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


def add_mux_to_link(proxy: dict) -> str:
    out = {}
    add_mux_to_dict(out, proxy)
    return hutils.encode.convert_dict_to_url(out)


def add_mux_to_dict(d: dict, proxy):
    if proxy.get('mux_enable'):
        # according to github.com/hiddify/ray2sing/
        d['muxtype'] = proxy["mux_protocol"]
        d['muxmaxc'] = proxy["mux_max_connections"]
        d['mux'] = proxy['mux_min_streams']
        d['muxsmax'] = proxy["mux_max_streams"]
        d['muxpad'] = proxy["mux_padding_enable"]

        if proxy.get('mux_brutal_enable'):
            d['muxup'] = proxy["mux_brutal_up_mbps"]
            d['muxdown'] = proxy["mux_brutal_down_mbps"]
