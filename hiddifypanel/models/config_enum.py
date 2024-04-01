from enum import auto, Enum
from typing import Union

from strenum import StrEnum
from fast_enum import FastEnum


class HEnum(StrEnum):
    @classmethod
    def from_str(cls, key: str) -> 'HEnum':
        return cls[key]


class Lang(HEnum):
    en = auto()
    fa = auto()
    ru = auto()
    pt = auto()
    zh = auto()


class PanelMode(HEnum):
    standalone = auto()
    parent = auto()
    child = auto()


class LogLevel(HEnum):
    TRACE = auto()
    DEBUG = auto()
    INFO = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class ConfigCategory(StrEnum):
    admin = auto()
    branding = auto()
    general = auto()
    proxies = auto()
    domain_fronting = auto()
    telegram = auto()
    http = auto()
    tls = auto()
    mux = auto()
    tls_trick = auto()
    ssh = auto()
    ssfaketls = auto()
    shadowtls = auto()
    restls = auto()
    tuic = auto()
    hysteria = auto()
    ssr = auto()
    kcp = auto()
    hidden = auto()
    advanced = auto()
    too_advanced = auto()
    warp = auto()
    reality = auto()
    wireguard = auto()
    shadowsocks = auto()


class ApplyMode(StrEnum):
    apply = auto()
    restart = auto()
    nothing = auto()


def _BoolConfigDscr(category: ConfigCategory, apply_mode: ApplyMode = ApplyMode.nothing, show_in_parent: bool = True, hide_in_virtual_child=False):
    return category, apply_mode, bool, show_in_parent


def _StrConfigDscr(category: ConfigCategory, apply_mode: ApplyMode = ApplyMode.nothing, show_in_parent: bool = True, hide_in_virtual_child=False):
    return category, apply_mode, str, show_in_parent


def _IntConfigDscr(category: ConfigCategory, apply_mode: ApplyMode = ApplyMode.nothing, show_in_parent: bool = True, hide_in_virtual_child=False):
    return category, apply_mode, int, show_in_parent


def _TypedConfigDscr(ctype: type, category: ConfigCategory, apply_mode: ApplyMode = ApplyMode.nothing, show_in_parent: bool = True, hide_in_virtual_child=False):
    return category, apply_mode, ctype, show_in_parent


class ConfigEnum(metaclass=FastEnum):
    # category: ConfigCategory
    __slots__ = ('name', 'value', 'category', 'apply_mode', 'type', 'show_in_parent', 'hide_in_virtual_child')

    def __init__(self, category: ConfigCategory, apply_mode: ApplyMode = ApplyMode.apply, ctype=type, show_in_parent: bool = True, hide_in_virtual_child=False, name=auto):
        self.value = name
        self.name = name
        self.category = category
        self.apply_mode = apply_mode
        self.type = ctype
        self.show_in_parent = show_in_parent
        self.hide_in_virtual_child = hide_in_virtual_child

    @classmethod
    def dbvalues(cls):
        return {c.name: c for c in ConfigEnum}
    create_easysetup_link = _BoolConfigDscr(ConfigCategory.hidden, ApplyMode.apply, hide_in_virtual_child=True)
    wireguard_enable = _BoolConfigDscr(ConfigCategory.wireguard, ApplyMode.apply, hide_in_virtual_child=True)
    wireguard_port = _StrConfigDscr(ConfigCategory.wireguard, ApplyMode.apply, hide_in_virtual_child=True)
    wireguard_ipv6 = _StrConfigDscr(ConfigCategory.hidden, ApplyMode.apply, hide_in_virtual_child=True)
    wireguard_ipv4 = _StrConfigDscr(ConfigCategory.hidden, ApplyMode.apply, hide_in_virtual_child=True)
    wireguard_private_key = _StrConfigDscr(ConfigCategory.hidden, ApplyMode.apply, hide_in_virtual_child=True)
    wireguard_public_key = _StrConfigDscr(ConfigCategory.hidden, ApplyMode.apply, hide_in_virtual_child=True)
    wireguard_noise_trick = _StrConfigDscr(ConfigCategory.wireguard, ApplyMode.apply)

    ssh_server_redis_url = _StrConfigDscr(ConfigCategory.hidden, hide_in_virtual_child=True)
    ssh_server_port = _StrConfigDscr(ConfigCategory.ssh, ApplyMode.apply, hide_in_virtual_child=True)
    ssh_server_enable = _BoolConfigDscr(ConfigCategory.ssh, ApplyMode.apply)
    first_setup = _BoolConfigDscr(ConfigCategory.hidden)
    core_type = _StrConfigDscr(ConfigCategory.advanced, ApplyMode.apply, hide_in_virtual_child=True)
    warp_enable = _BoolConfigDscr(ConfigCategory.hidden, ApplyMode.restart, hide_in_virtual_child=True)
    warp_mode = _StrConfigDscr(ConfigCategory.warp, ApplyMode.apply, hide_in_virtual_child=True)
    warp_plus_code = _StrConfigDscr(ConfigCategory.warp, ApplyMode.apply, hide_in_virtual_child=True)
    warp_sites = _StrConfigDscr(ConfigCategory.warp, ApplyMode.apply, hide_in_virtual_child=True)
    dns_server = _StrConfigDscr(ConfigCategory.general, ApplyMode.apply, hide_in_virtual_child=True)
    reality_fallback_domain = _StrConfigDscr(ConfigCategory.hidden, ApplyMode.apply)  # removed
    reality_server_names = _StrConfigDscr(ConfigCategory.hidden, ApplyMode.apply)  # removed
    reality_short_ids = _StrConfigDscr(ConfigCategory.reality, ApplyMode.apply, hide_in_virtual_child=True)
    reality_private_key = _StrConfigDscr(ConfigCategory.reality, ApplyMode.apply, hide_in_virtual_child=True)
    reality_public_key = _StrConfigDscr(ConfigCategory.reality, ApplyMode.apply, hide_in_virtual_child=True)
    reality_port = _StrConfigDscr(ConfigCategory.reality, ApplyMode.apply, hide_in_virtual_child=True)

    restls1_2_domain = _StrConfigDscr(ConfigCategory.hidden)
    restls1_3_domain = _StrConfigDscr(ConfigCategory.hidden)
    show_usage_in_sublink = _BoolConfigDscr(ConfigCategory.general)
    cloudflare = _StrConfigDscr(ConfigCategory.too_advanced, ApplyMode.apply)
    license = _StrConfigDscr(ConfigCategory.hidden)
    country = _StrConfigDscr(ConfigCategory.general, ApplyMode.restart, hide_in_virtual_child=True)
    package_mode = _StrConfigDscr(ConfigCategory.advanced, hide_in_virtual_child=True)
    utls = _StrConfigDscr(ConfigCategory.advanced)
    telegram_bot_token = _StrConfigDscr(ConfigCategory.telegram, ApplyMode.apply, hide_in_virtual_child=True)

    # region child-parent
    # deprecated
    is_parent = _BoolConfigDscr(ConfigCategory.hidden)
    # parent panel domain
    parent_panel = _StrConfigDscr(ConfigCategory.hidden)  # should be able to change by user
    parent_domain = _StrConfigDscr(ConfigCategory.hidden)
    parent_admin_proxy_path = _StrConfigDscr(ConfigCategory.hidden)

    # the panel mode could be one of these: "parent", "child", "standalone"
    # this config value would be 'standalone' by default. and would be set by panel itself
    panel_mode = _TypedConfigDscr(PanelMode, ConfigCategory.hidden, ApplyMode.nothing, hide_in_virtual_child=True)
    # endregion

    log_level = _TypedConfigDscr(LogLevel, ConfigCategory.hidden, ApplyMode.restart, hide_in_virtual_child=True)

    unique_id = _StrConfigDscr(ConfigCategory.hidden)
    last_hash = _StrConfigDscr(ConfigCategory.hidden)
    cdn_forced_host = _StrConfigDscr(ConfigCategory.hidden)  # removed
    lang = _TypedConfigDscr(Lang, ConfigCategory.branding)
    admin_lang = _TypedConfigDscr(Lang, ConfigCategory.admin)
    admin_secret = _StrConfigDscr(ConfigCategory.hidden)  # removed

    # tls
    tls_ports = _StrConfigDscr(ConfigCategory.tls, ApplyMode.apply)

    tls_fragment_enable = _BoolConfigDscr(ConfigCategory.tls_trick, ApplyMode.apply)
    tls_fragment_size = _StrConfigDscr(ConfigCategory.tls_trick, ApplyMode.apply)
    tls_fragment_sleep = _StrConfigDscr(ConfigCategory.tls_trick, ApplyMode.apply)
    tls_mixed_case = _BoolConfigDscr(ConfigCategory.tls_trick, ApplyMode.apply)
    tls_padding_enable = _BoolConfigDscr(ConfigCategory.tls_trick, ApplyMode.apply)
    tls_padding_length = _StrConfigDscr(ConfigCategory.tls_trick, ApplyMode.apply)

    # mux
    mux_enable = _BoolConfigDscr(ConfigCategory.mux, ApplyMode.apply)
    mux_protocol = _StrConfigDscr(ConfigCategory.mux, ApplyMode.apply)
    mux_max_connections = _IntConfigDscr(ConfigCategory.mux, ApplyMode.apply)
    mux_min_streams = _IntConfigDscr(ConfigCategory.mux, ApplyMode.apply)
    mux_max_streams = _IntConfigDscr(ConfigCategory.mux, ApplyMode.apply)
    mux_padding_enable = _BoolConfigDscr(ConfigCategory.mux, ApplyMode.apply)
    mux_brutal_enable = _BoolConfigDscr(ConfigCategory.mux, ApplyMode.apply)
    mux_brutal_up_mbps = _IntConfigDscr(ConfigCategory.mux, ApplyMode.apply)
    mux_brutal_down_mbps = _IntConfigDscr(ConfigCategory.mux, ApplyMode.apply)

    http_ports = _StrConfigDscr(ConfigCategory.http, ApplyMode.apply)
    kcp_ports = _StrConfigDscr(ConfigCategory.hidden, ApplyMode.apply)
    kcp_enable = _BoolConfigDscr(ConfigCategory.hidden, ApplyMode.apply)
    decoy_domain = _StrConfigDscr(ConfigCategory.general, ApplyMode.apply, hide_in_virtual_child=True)
    # will be deprecated
    proxy_path = _StrConfigDscr(ConfigCategory.hidden, ApplyMode.apply, hide_in_virtual_child=True)
    proxy_path_admin = _StrConfigDscr(ConfigCategory.too_advanced, ApplyMode.apply, hide_in_virtual_child=True)
    proxy_path_client = _StrConfigDscr(ConfigCategory.too_advanced, ApplyMode.apply, hide_in_virtual_child=True)
    firewall = _BoolConfigDscr(ConfigCategory.general, ApplyMode.apply, hide_in_virtual_child=True)
    netdata = _BoolConfigDscr(ConfigCategory.hidden, ApplyMode.apply)  # removed
    http_proxy_enable = _BoolConfigDscr(ConfigCategory.http)
    block_iran_sites = _BoolConfigDscr(ConfigCategory.proxies, ApplyMode.apply, hide_in_virtual_child=True)
    allow_invalid_sni = _BoolConfigDscr(ConfigCategory.tls, ApplyMode.apply, hide_in_virtual_child=True)
    auto_update = _BoolConfigDscr(ConfigCategory.general, ApplyMode.apply, True, hide_in_virtual_child=True)
    speed_test = _BoolConfigDscr(ConfigCategory.general, ApplyMode.apply, hide_in_virtual_child=True)
    only_ipv4 = _BoolConfigDscr(ConfigCategory.general, ApplyMode.apply, hide_in_virtual_child=True)

    shared_secret = _StrConfigDscr(ConfigCategory.proxies, ApplyMode.apply, hide_in_virtual_child=True)

    telegram_enable = _BoolConfigDscr(ConfigCategory.telegram, ApplyMode.restart)
    # telegram_secret=auto()
    telegram_adtag = _StrConfigDscr(ConfigCategory.telegram, ApplyMode.restart, hide_in_virtual_child=True)
    telegram_lib = _StrConfigDscr(ConfigCategory.telegram, ApplyMode.restart, hide_in_virtual_child=True)
    telegram_fakedomain = _StrConfigDscr(ConfigCategory.telegram, ApplyMode.restart, hide_in_virtual_child=True)

    v2ray_enable = _BoolConfigDscr(ConfigCategory.hidden, ApplyMode.apply)
    torrent_block = _BoolConfigDscr(ConfigCategory.general, ApplyMode.apply)

    tuic_enable = _BoolConfigDscr(ConfigCategory.hidden, ApplyMode.apply)
    tuic_port = _StrConfigDscr(ConfigCategory.hidden, ApplyMode.apply, hide_in_virtual_child=True)

    # the hysteria is refereing to hysteria2
    hysteria_enable = _BoolConfigDscr(ConfigCategory.hidden, ApplyMode.apply)
    hysteria_port = _StrConfigDscr(ConfigCategory.hidden, ApplyMode.apply, hide_in_virtual_child=True)
    # if be enable hysteria2 will be use salamander as obfs
    hysteria_obfs_enable = _BoolConfigDscr(ConfigCategory.hysteria, ApplyMode.apply)
    hysteria_up_mbps = _StrConfigDscr(ConfigCategory.hysteria, ApplyMode.apply)
    hysteria_down_mbps = _StrConfigDscr(ConfigCategory.hysteria, ApplyMode.apply)

    shadowsocks2022_enable = _BoolConfigDscr(ConfigCategory.shadowsocks, ApplyMode.apply)
    shadowsocks2022_method = _StrConfigDscr(ConfigCategory.shadowsocks, ApplyMode.apply)
    shadowsocks2022_port = _StrConfigDscr(ConfigCategory.shadowsocks, ApplyMode.apply)
    ssfaketls_enable = _BoolConfigDscr(ConfigCategory.shadowsocks, ApplyMode.apply)
    ssfaketls_fakedomain = _StrConfigDscr(ConfigCategory.shadowsocks, ApplyMode.apply, hide_in_virtual_child=True)
    shadowtls_enable = _BoolConfigDscr(ConfigCategory.shadowsocks, ApplyMode.apply)
    shadowtls_fakedomain = _StrConfigDscr(ConfigCategory.shadowsocks, ApplyMode.apply, hide_in_virtual_child=True)

    ssr_enable = _BoolConfigDscr(ConfigCategory.hidden, ApplyMode.apply)
    # ssr_secret="ssr_secret"
    ssr_fakedomain = _StrConfigDscr(ConfigCategory.hidden, ApplyMode.apply)

    vmess_enable = _BoolConfigDscr(ConfigCategory.proxies, ApplyMode.apply)
    domain_fronting_domain = _StrConfigDscr(ConfigCategory.hidden)  # removed
    domain_fronting_http_enable = _BoolConfigDscr(ConfigCategory.hidden, ApplyMode.apply)  # removed
    domain_fronting_tls_enable = _BoolConfigDscr(ConfigCategory.hidden, ApplyMode.apply)  # removed

    ws_enable = _BoolConfigDscr(ConfigCategory.proxies, ApplyMode.apply)
    grpc_enable = _BoolConfigDscr(ConfigCategory.proxies, ApplyMode.apply)
    httpupgrade_enable = _BoolConfigDscr(ConfigCategory.proxies, ApplyMode.apply)
    vless_enable = _BoolConfigDscr(ConfigCategory.proxies, ApplyMode.apply)
    trojan_enable = _BoolConfigDscr(ConfigCategory.proxies, ApplyMode.apply)
    reality_enable = _BoolConfigDscr(ConfigCategory.proxies, ApplyMode.apply)
    tcp_enable = _BoolConfigDscr(ConfigCategory.proxies, ApplyMode.apply)
    quic_enable = _BoolConfigDscr(ConfigCategory.proxies, ApplyMode.apply)
    xtls_enable = _BoolConfigDscr(ConfigCategory.proxies, ApplyMode.apply)
    h2_enable = _BoolConfigDscr(ConfigCategory.proxies, ApplyMode.apply)

    db_version = _StrConfigDscr(ConfigCategory.hidden, ApplyMode.apply)

    branding_title = _StrConfigDscr(ConfigCategory.branding)
    branding_site = _StrConfigDscr(ConfigCategory.branding)
    branding_freetext = _StrConfigDscr(ConfigCategory.branding)
    not_found = _StrConfigDscr(ConfigCategory.hidden)
    path_vmess = _StrConfigDscr(ConfigCategory.too_advanced, hide_in_virtual_child=True)
    path_vless = _StrConfigDscr(ConfigCategory.too_advanced, hide_in_virtual_child=True)
    path_trojan = _StrConfigDscr(ConfigCategory.too_advanced, hide_in_virtual_child=True)
    path_v2ray = _StrConfigDscr(ConfigCategory.hidden, hide_in_virtual_child=True)  # deprecated
    path_ss = _StrConfigDscr(ConfigCategory.hidden, hide_in_virtual_child=True)

    path_httpupgrade = _StrConfigDscr(ConfigCategory.too_advanced, hide_in_virtual_child=True)
    path_ws = _StrConfigDscr(ConfigCategory.too_advanced, hide_in_virtual_child=True)
    path_tcp = _StrConfigDscr(ConfigCategory.too_advanced, hide_in_virtual_child=True)
    path_grpc = _StrConfigDscr(ConfigCategory.too_advanced, hide_in_virtual_child=True)

    @classmethod
    def __missing__(cls, value):
        return ConfigEnum.not_found

    def __contains__(self, other):
        return other in self.name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return f'{self}' == f'{other}'

    def __neg__(self, other):
        return not self.__eq__(other)

    def endswith(self, other):
        return self.name.endswith(other)  # type: ignore

    def startswith(self, other):
        return self.name.startswith(other)  # type: ignore
