from sqlalchemy_serializer import SerializerMixin


from flask import Markup
from dateutil import relativedelta
from hiddifypanel.panel.database import db
import enum,datetime
import uuid as uuid_mod
from enum import auto
from strenum import StrEnum
class ConfigEnum(StrEnum):
    lang='lang'
    admin_secret="admin_secret"
    tls_ports="tls_ports"
    http_ports="http_ports"
    kcp_ports="kcp_ports"
    kcp_enable="kcp_enable"
    decoy_site="decoy_site"
    proxy_path="proxy_path"
    firewall="firewall"
    netdata="netdata"
    http_proxy_enable="http_proxy_enable"
    block_iran_sites="block_iran_sites"
    allow_invalid_sni="allow_invalid_sni"
    auto_update="auto_update"
    speed_test="speed_test"
    only_ipv4="only_ipv4"

    shared_secret="shared_secret"

    telegram_enable="telegram_enable"
    # telegram_secret="telegram_secret"
    telegram_adtag="telegram_adtag"
    telegram_fakedomain="telegram_fakedomain"

    ssfaketls_enable="ssfaketls_enable"
    # ssfaketls_secret="ssfaketls_secret"
    ssfaketls_fakedomain="ssfaketls_fakedomain"
    
    shadowtls_enable="shadowtls_enable"
    # shadowtls_secret="shadowtls_secret"
    shadowtls_fakedomain="shadowtls_fakedomain"

    tuic_enable="tuic_enable"
    tuic_port="tuic_port"

    ssr_enable="ssr_enable"
    # ssr_secret="ssr_secret"
    ssr_fakedomain="ssr_fakedomain"

    vmess_enable="vmess_enable"
    domain_fronting_domain="domain_fronting_domain"
    domain_fronting_http_enable="domain_fronting_http_enable"
    domain_fronting_tls_enable="domain_fronting_tls_enable"

    db_version="db_version"

    
class DomainType(enum.Enum):
    direct = "direct"
    cdn = "cdn"
    # fake_cdn = "fake_cdn"
    # telegram_faketls = "telegram_faketls"
    # ss_faketls = "ss_faketls"

class Domain(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    domain = db.Column(db.String(200),nullable=False,unique=True)
    mode = db.Column(db.Enum(DomainType),nullable=False)

class Proxy(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200),nullable=False,unique=True)
    enable = db.Column(db.Boolean,nullable=False)
    proto = db.Column(db.String(200),nullable=False)
    l3 = db.Column(db.String(200),nullable=False)
    transport= db.Column(db.String(200),nullable=False)
    cdn= db.Column(db.String(200),nullable=False)

class User(db.Model, SerializerMixin):
    
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), default=lambda: str(uuid_mod.uuid4()),nullable=False,unique=True)
    # uuid = db.Column(db.UUID(binary=False),default=uuid.uuid4,unique=True,nullable=False)
    name = db.Column(db.String(512),nullable=False)
    # monthly_usage_limit=db.Column(db.BigInteger,default=100,nullable=False)
    # current_usage=db.Column(db.BigInteger,default=0,nullable=False)
    monthly_usage_limit_GB=db.Column(db.Numeric(6,9, asdecimal=False),default=1000,nullable=False)
    current_usage_GB=db.Column(db.Numeric(6,9, asdecimal=False),default=0,nullable=False)
    
    
    expiry_time=db.Column(db.Date, default= datetime.date.today() + relativedelta.relativedelta(months=6)) 
    last_reset_time=db.Column(db.Date, default=datetime.date.today()) 
    
        

class BoolConfig(db.Model, SerializerMixin):
    category = db.Column(db.String(128), primary_key=True)
    key = db.Column(db.String(128), primary_key=True)
    value = db.Column(db.Boolean)
    description=db.Column(db.String(512))
    
class StrConfig(db.Model, SerializerMixin):
    category = db.Column(db.String(128), primary_key=True)
    key = db.Column(db.String(128), primary_key=True)
    value = db.Column(db.String(512))
    description=db.Column(db.String(512))

def hdomains(mode):
    domains=Domain.query.filter(Domain.mode==mode).all()
    if domains:
        return [d.domain for d in domains]
    return []

def hdomain(mode):
    domains=hdomains(mode)
    if domains:
        return domains[0]
    return None

def get_hdomains():
    return { mode: hdomains(mode) for mode in DomainType}    


def hconfig(key:ConfigEnum):
    try:
        str_conf= StrConfig.query.filter(StrConfig.key==key).first()
        if str_conf:
            return str_conf.value
        bool_conf=BoolConfig.query.filter(BoolConfig.key==key).first()
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
    return {**{u.key:u.value for u in BoolConfig.query.all()},
            **{u.key:u.value for u in StrConfig.query.all()},
            # ConfigEnum.telegram_fakedomain:hdomain(DomainType.telegram_faketls),
            # ConfigEnum.ssfaketls_fakedomain:hdomain(DomainType.ss_faketls),
            # ConfigEnum.fake_cdn_domain:hdomain(DomainType.fake_cdn)
            }
    
