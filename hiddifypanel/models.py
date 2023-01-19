from sqlalchemy_serializer import SerializerMixin
from flask import Markup

from hiddifypanel.panel.database import db
import enum,uuid,datetime
from enum import auto
class ConfigEnum:
    admin_secret="admin_secret"
    tls_ports="tls_ports"
    http_ports="http_ports"
    kcp_ports="kcp_ports"
    decoy_site="decoy_site"
    proxy_path="proxy_path"
    firewall="firewall"
    netdata="netdata"
    http_proxy="http_proxy"
    block_iran_sites="block_iran_sites"
    allow_invalid_sni="allow_invalid_sni"
    auto_update="auto_update"
    speed_test="speed_test"
    only_ipv4="only_ipv4"
    telegram_enable="telegram_enable"
    telegram_secret="telegram_secret"
    telegram_adtag="telegram_adtag"
    telegram_fakedomain="telegram_fakedomain"
    ssfaketls_enable="ssfaketls_enable"
    ssfaketls_secret="ssfaketls_secret"
    ssfaketls_fakedomain="ssfaketls_fakedomain"
    vmess_enable="vmess_enable"
    fake_cdn_domain="fake_cdn_domain"

    
class DomainType(enum.Enum):
    direct = "direct"
    cdn = "cdn"
    fake_cdn = "fake_cdn"
    telegram_faketls = "telegram_faketls"
    ss_faketls = "ss_faketls"

class Domain(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    domain = db.Column(db.String(200),nullable=False,unique=True)
    mode = db.Column(db.Enum(DomainType),nullable=False)


class User(db.Model, SerializerMixin):
    
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()),nullable=False,unique=True)
    # uuid = db.Column(db.UUID(binary=False),default=uuid.uuid4,unique=True,nullable=False)
    name = db.Column(db.String(512),nullable=False)
    # monthly_usage_limit=db.Column(db.BigInteger,default=100,nullable=False)
    # current_usage=db.Column(db.BigInteger,default=0,nullable=False)
    monthly_usage_limit_GB=db.Column(db.Numeric(6,9, asdecimal=False),default=100,nullable=False)
    current_usage_GB=db.Column(db.Numeric(6,9, asdecimal=False),default=0,nullable=False)
    from dateutil import relativedelta
    next6month = datetime.date.today() + relativedelta.relativedelta(months=6)
    expiry_time=db.Column(db.Date, default=next6month) 
    
        

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


def hconfig(key):
    str_conf= StrConfig.query.filter(StrConfig.key==key).first()
    if str_conf:
        return str_conf.value
    bool_conf=BoolConfig.query.filter(StrConfig.key==key).first()
    if bool_conf:
        return bool_conf.value
    if key == ConfigEnum.ssfaketls_fakedomain:
        return hdomain(DomainType.ss_faketls)
    if key == ConfigEnum.telegram_fakedomain:
        return hdomain(DomainType.telegram_faketls)
    if key == ConfigEnum.fake_cdn_domain:
        return hdomain(DomainType.fake_cdn)

    return None

def get_hconfigs():
    return {**{u.key:u.value for u in BoolConfig.query.all()},
            **{u.key:u.value for u in StrConfig.query.all()},
            ConfigEnum.telegram_fakedomain:hdomain(DomainType.telegram_faketls),
            ConfigEnum.ssfaketls_fakedomain:hdomain(DomainType.ss_faketls),
            ConfigEnum.fake_cdn_domain:hdomain(DomainType.fake_cdn)
            }
    
