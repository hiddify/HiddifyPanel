from sqlalchemy_serializer import SerializerMixin


from flask import Markup
from dateutil import relativedelta
from hiddifypanel.panel.database import db
import enum
import datetime
import uuid as uuid_mod
from enum import auto
from strenum import StrEnum


class ConfigEnum(StrEnum):
    lang = auto()
    admin_secret = auto()
    tls_ports = auto()
    http_ports = auto()
    kcp_ports = auto()
    kcp_enable = auto()
    decoy_site = auto()
    proxy_path = auto()
    firewall = auto()
    netdata = auto()
    http_proxy_enable = auto()
    block_iran_sites = auto()
    allow_invalid_sni = auto()
    auto_update = auto()
    speed_test = auto()
    only_ipv4 = auto()

    shared_secret = auto()

    telegram_enable = auto()
    # telegram_secret=auto()
    telegram_adtag = auto()
    telegram_fakedomain = auto()

    ssfaketls_enable = auto()
    # ssfaketls_secret="ssfaketls_secret"
    ssfaketls_fakedomain = auto()

    shadowtls_enable = auto()
    # shadowtls_secret=auto()
    shadowtls_fakedomain = auto()

    tuic_enable = auto()
    tuic_port = auto()

    ssr_enable = auto()
    # ssr_secret="ssr_secret"
    ssr_fakedomain = auto()

    vmess_enable = auto()
    domain_fronting_domain = auto()
    domain_fronting_http_enable = auto()
    domain_fronting_tls_enable = auto()

    db_version = auto()
    not_found=auto()
    @classmethod
    def _missing_(cls, value):
      return cls.not_found #"key not found"
    def info(self):
        map = {
            lang: {'category': 'general'},
            admin_secret: {'category': 'admin'},
            tls_ports: {'category': 'tls'},
            http_ports: {'category': 'http'},
            kcp_ports: {'category': 'kcp'},
            kcp_enable: {'category': 'kcp'},
            decoy_site: {'category': 'general'},
            proxy_path: {'category': 'proxies'},
            firewall: {'category': 'general'},
            netdata: {'category': 'general'},
            http_proxy_enable: {'category': 'http'},
            block_iran_sites: {'category': 'proxies'},
            allow_invalid_sni: {'category': 'tls'},
            auto_update: {'category': 'general'},
            speed_test: {'category': 'general'},
            only_ipv4: {'category': 'general'},

            shared_secret: {'category': 'proxies'},

            telegram_enable: {'category': 'telegram'},
            # telegram_secret:{'category':'general'},
            telegram_adtag: {'category': 'telegram'},
            telegram_fakedomain: {'category': 'telegram'},

            ssfaketls_enable: {'category': 'ssfaketls'},
            # ssfaketls_secret:{'category':'ssfaketls'},
            ssfaketls_fakedomain: {'category': 'ssfaketls'},

            shadowtls_enable: {'category': 'shadowtls'},
            # shadowtls_secret:{'category':'shadowtls'},
            shadowtls_fakedomain: {'category': 'shadowtls'},

            tuic_enable: {'category': 'tuic'},
            tuic_port: {'category': 'tuic'},

            ssr_enable: {'category': 'ssr'},
            # ssr_secret:{'category':'ssr'},
            ssr_fakedomain: {'category': 'ssr'},

            vmess_enable: {'category': 'proxies'},
            domain_fronting_domain: {'category': 'domain_fronting'},
            domain_fronting_http_enable: {'category': 'domain_fronting'},
            domain_fronting_tls_enable: {'category': 'domain_fronting'},

            db_version: {'category': 'hidden'},
        }
        return map[self]


class DomainType(enum.Enum):
    direct = "direct"
    cdn = "cdn"
    # fake_cdn = "fake_cdn"
    # telegram_faketls = "telegram_faketls"
    # ss_faketls = "ss_faketls"


class Domain(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    domain = db.Column(db.String(200), nullable=False, unique=True)
    mode = db.Column(db.Enum(DomainType), nullable=False)


class Proxy(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    enable = db.Column(db.Boolean, nullable=False)
    proto = db.Column(db.String(200), nullable=False)
    l3 = db.Column(db.String(200), nullable=False)
    transport = db.Column(db.String(200), nullable=False)
    cdn = db.Column(db.String(200), nullable=False)


class User(db.Model, SerializerMixin):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), default=lambda: str(
        uuid_mod.uuid4()), nullable=False, unique=True)
    # uuid = db.Column(db.UUID(binary=False),default=uuid.uuid4,unique=True,nullable=False)
    name = db.Column(db.String(512), nullable=False)
    # monthly_usage_limit=db.Column(db.BigInteger,default=100,nullable=False)
    # current_usage=db.Column(db.BigInteger,default=0,nullable=False)
    monthly_usage_limit_GB = db.Column(db.Numeric(
        6, 9, asdecimal=False), default=1000, nullable=False)
    current_usage_GB = db.Column(db.Numeric(
        6, 9, asdecimal=False), default=0, nullable=False)

    expiry_time = db.Column(
        db.Date, default=datetime.date.today() + relativedelta.relativedelta(months=6))
    last_reset_time = db.Column(db.Date, default=datetime.date.today())


class BoolConfig(db.Model, SerializerMixin):
    category = db.Column(db.String(128), primary_key=True)
    key = db.Column(db.Enum(ConfigEnum), primary_key=True)
    value = db.Column(db.Boolean)
    description = db.Column(db.String(512))


class StrConfig(db.Model, SerializerMixin):
    category = db.Column(db.String(128), primary_key=True)
    key = db.Column(db.Enum(ConfigEnum), primary_key=True,   default=ConfigEnum.admin_secret)
    value = db.Column(db.String(512))
    description = db.Column(db.String(512))


def hdomains(mode):
    domains = Domain.query.filter(Domain.mode == mode).all()
    if domains:
        return [d.domain for d in domains]
    return []


def hdomain(mode):
    domains = hdomains(mode)
    if domains:
        return domains[0]
    return None


def get_hdomains():
    return {mode: hdomains(mode) for mode in DomainType}


def hconfig(key: ConfigEnum):
    try:
        str_conf = StrConfig.query.filter(StrConfig.key == key).first()
        if str_conf:
            return str_conf.value
        bool_conf = BoolConfig.query.filter(BoolConfig.key == key).first()
        if bool_conf:
            return bool_conf.value
        # if key == ConfigEnum.ssfaketls_fakedomain:
        #     return hdomain(DomainType.ss_faketls)
        # if key == ConfigEnum.telegram_fakedomain:
        #     return hdomain(DomainType.telegram_faketls)
        # if key == ConfigEnum.fake_cdn_domain:
        #     return hdomain(DomainType.fake_cdn)
    except:
        print(f'{key} error!')

    return None


def get_hconfigs():
    return {**{u.key: u.value for u in BoolConfig.query.all()},
            **{u.key: u.value for u in StrConfig.query.all()},
            # ConfigEnum.telegram_fakedomain:hdomain(DomainType.telegram_faketls),
            # ConfigEnum.ssfaketls_fakedomain:hdomain(DomainType.ss_faketls),
            # ConfigEnum.fake_cdn_domain:hdomain(DomainType.fake_cdn)
            }
