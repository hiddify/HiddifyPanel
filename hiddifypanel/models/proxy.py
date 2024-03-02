from enum import auto

from sqlalchemy_serializer import SerializerMixin
from strenum import StrEnum

from hiddifypanel.database import db


class ProxyTransport(StrEnum):
    h2 = auto()
    grpc = auto()
    XTLS = auto()
    faketls = auto()
    shadowtls = auto()
    restls1_2 = auto()
    restls1_3 = auto()
    # h1=auto()
    WS = auto()
    tcp = auto()
    ssh = auto()
    httpupgrade = auto()
    custom = auto()
    shadowsocks = auto()


class ProxyCDN(StrEnum):
    CDN = auto()
    direct = auto()
    Fake = auto()
    relay = auto()


class ProxyProto(StrEnum):
    vless = auto()
    trojan = auto()
    vmess = auto()
    ss = auto()
    v2ray = auto()
    ssr = auto()
    ssh = auto()
    tuic = auto()
    # hysteria = auto()
    hysteria2 = auto()
    wireguard = auto()


class ProxyL3(StrEnum):
    tls = auto()
    tls_h2 = auto()
    tls_h2_h1 = auto()
    h3_quic = auto()
    reality = auto()
    http = auto()
    kcp = auto()
    ssh = auto()
    udp = auto()
    custom = auto()


class Proxy(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), default=0)
    name = db.Column(db.String(200), nullable=False, unique=False)
    enable = db.Column(db.Boolean, nullable=False)
    proto = db.Column(db.Enum(ProxyProto), nullable=False)
    l3 = db.Column(db.Enum(ProxyL3), nullable=False)
    transport = db.Column(db.Enum(ProxyTransport), nullable=False)
    cdn = db.Column(db.Enum(ProxyCDN), nullable=False)

    @property
    def enabled(self):
        return self.enable * 1

    def to_dict(self):
        return {
            'name': self.name,
            'enable': self.enable,
            'proto': self.proto,
            'l3': self.l3,
            'transport': self.transport,
            'cdn': self.cdn,
            'child_unique_id': self.child.unique_id if self.child else ''
        }

    @staticmethod
    def add_or_update(commit=True, child_id=0, **proxy):
        dbproxy = Proxy.query.filter(Proxy.name == proxy['name']).first()
        if not dbproxy:
            dbproxy = Proxy()
            db.session.add(dbproxy)
        dbproxy.enable = proxy['enable']
        dbproxy.name = proxy['name']
        dbproxy.proto = proxy['proto']
        dbproxy.transport = proxy['transport']
        dbproxy.cdn = proxy['cdn']
        dbproxy.l3 = proxy['l3']
        dbproxy.child_id = child_id
        if commit:
            db.session.commit()

    @staticmethod
    def bulk_register(proxies, commit=True, override_child_unique_id=None):
        from hiddifypanel.panel import hiddify
        for proxy in proxies:
            child_id = hiddify.get_child(unique_id=None)
            Proxy.add_or_update(commit=False, child_id=child_id, **proxy)
        if commit:
            db.session.commit()

    def __str__(self):
        return str(self.to_dict())
