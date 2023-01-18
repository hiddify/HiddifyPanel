from sqlalchemy_serializer import SerializerMixin

from hiddifypanel.panel.database import db
import enum
from enum import auto
class ConfigEnum:
    admin_secret="admin_secret"
    tls_ports="tls_ports"
    http_ports="http_ports"
    decoy_site="decoy_site"
    proxy_path="proxy_path"
    firewall="firewall"
    netdata="netdata"
    http_proxy="http_proxy"
    iran_sites="iran_sites"
    allow_invalid_sni="allow_invalid_sni"
    auto_update="auto_update"
    speed_test="speed_test"
    only_ipv4="only_ipv4"
    telegram_enable="telegram_enable"
    telegram_secret="telegram_secret"
    telegram_adtag="telegram_adtag"
    ssfaketls_enable="ssfaketls_enable"
    ssfaketls_secret="ssfaketls_secret"
    
class DomainType(enum.Enum):
    direct = 1
    cdn = 2
    fake_cdn = 3
    telegram_faketls = 4
    ss_faketls = 5

class Domain(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    domain = db.Column(db.String(200),nullable=False,unique=True)
    mode = db.Column(db.Enum(DomainType),nullable=False)

class User(db.Model, SerializerMixin):
    uuid = db.Column(db.String(32),primary_key=True,nullable=False,unique=True)
    alias = db.Column(db.String(512),nullable=False)
    monthly_usage_limit=db.Column(db.BigInteger,nullable=False)
    current_usage=db.Column(db.BigInteger,nullable=False)
    expiry_time=db.Date()

class Config(db.Model, SerializerMixin):
    key = db.Column(db.String(128), primary_key=True)
    boolval = db.Column(db.Boolean)
    value = db.Column(db.String(512))
    
