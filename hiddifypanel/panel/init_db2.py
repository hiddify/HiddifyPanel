from hiddifypanel.models import  *
from hiddifypanel.panel.database import db
import sys
from hiddifypanel import Events        



from dateutil import relativedelta
import datetime

from hiddifypanel.panel import hiddify
import random
import uuid
import urllib
import string
from hiddifypanel import Events
from hiddifypanel.models import  *
from hiddifypanel.panel.database import db
import sys
from hiddifypanel import Events        
from dateutil import relativedelta
import datetime
from hiddifypanel.panel import hiddify
from hiddifypanel.panel.hiddify import get_random_domains,get_random_string
import random, uuid, urllib, string
from hiddifypanel import Events


def get_proxy_rows_v1():
    return make_proxy_rows([   
        # 'WS Fake vless',
        # 'WS Fake trojan',
        # 'WS Fake vmess',
        # 'grpc Fake vless',
        # 'grpc Fake trojan',
        # 'grpc Fake vmess',
        # "XTLS direct vless",
        # "XTLS direct trojan",
        "XTLS direct vless",      
        "WS direct vless",
        "WS direct trojan",
        "WS direct vmess",
        "WS CDN vless",
        "WS CDN trojan",
        "WS CDN vmess",
        "grpc CDN vless",
        "grpc CDN trojan",
        "grpc CDN vmess",
        "tcp direct vless",
        "tcp direct trojan",
        "tcp direct vmess",
        "grpc direct vless",
        "grpc direct trojan",
        "grpc direct vmess",
        # "h1 direct vless",
        # "h1 direct vmess",
        "faketls direct ss",
        "WS direct v2ray",
        "shadowtls direct ss",
        "restls1_2 direct ss",
        "restls1_3 direct ss",
        "tcp direct ssr",
        "WS CDN v2ray"]
    )

def make_proxy_rows(cfgs):
    for l3 in ["tls_h2","tls", "http", "kcp","reality"]:
        for c in cfgs:
            transport,cdn,proto=c.split(" ")
            if l3 in ["kcp",'reality'] and cdn!="direct":
                continue
            if l3=="reality" and ((transport not in ['tcp','grpc','XTLS']) or proto !='vless'):
                continue
            if proto=="trojan" and l3 not in ["tls",'xtls','tls_h2']:
                continue
            if transport in ["grpc","XTLS","faketls"] and l3=="http":
                continue
            # if l3 == "tls_h2" and transport =="grpc":
            #     continue
            enable=l3!="http" or proto=="vmess" 
            enable= enable and transport!='tcp'
            name=f'{l3} {c}'
            is_exist= Proxy.query.filter(Proxy.name==name).first() or Proxy.query.filter(Proxy.l3==l3,Proxy.transport==transport,Proxy.cdn==cdn,Proxy.proto==proto).first()        
            if not is_exist:
                yield Proxy(l3=l3,transport=transport,cdn=cdn,proto=proto,enable=enable,name=name)

def add_config_if_not_exist(key:ConfigEnum,val):
    table=BoolConfig if key.type()==bool else StrConfig
    if table.query.filter(table.key==key).count()==0:
        db.session.add(table(key=key,value=val,child_id=0))

def add_column(column):
    try:
        column_type = column.type.compile(db.engine.dialect)
        db.engine.execute(f'ALTER TABLE {column.table.name} ADD COLUMN {column.name} {column_type}')
    except:
        pass

def execute(query):
    try:
        db.engine.execute(query)
    except:
        pass    


# def remove_enums_without_related_ids_for_downgrade()
from .init_db import *
