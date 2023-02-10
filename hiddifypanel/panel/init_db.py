from hiddifypanel.models import  User,Domain,DomainType,BoolConfig,StrConfig,ConfigEnum,hconfig
from hiddifypanel.panel.database import db



from hiddifypanel.panel.database import db
from dateutil import relativedelta
import datetime
from hiddifypanel.models import BoolConfig,StrConfig,ConfigEnum,hconfig,Proxy
from hiddifypanel.models import Domain,DomainType
from hiddifypanel.models import User
from hiddifypanel.panel import hiddify
import random
import uuid
import urllib
import string

def get_random_string():
    # With combination of lower and upper case
    length=random.randint(10, 30)
    characters = string.ascii_letters + string.digits
    result_str = ''.join(random.choice(characters) for i in range(length))
    return result_str


def _v1():
        db.create_all()
        next10year = datetime.date.today() + relativedelta.relativedelta(years=6)
        external_ip=urllib.request.urlopen('https://v4.ident.me/').read().decode('utf8')
        
        data = [
            StrConfig(key=ConfigEnum.db_version,value=1),
            User(name="default",usage_limit_GB=9000,expiry_time=next10year),
            Domain(domain=external_ip+".sslip.io",mode=DomainType.direct),
            StrConfig(key=ConfigEnum.admin_secret,value=str(uuid.uuid4())),
            StrConfig(key=ConfigEnum.http_ports,value="80"),
            StrConfig(key=ConfigEnum.tls_ports,value="443"),
            
            StrConfig(key=ConfigEnum.decoy_domain,value="www.wikipedia.org"),
            StrConfig(key=ConfigEnum.proxy_path,value=get_random_string()),
            BoolConfig(key=ConfigEnum.firewall,value=False),
            BoolConfig(key=ConfigEnum.netdata,value=True),
            StrConfig(key=ConfigEnum.lang,value='en'),
            
            BoolConfig(key=ConfigEnum.block_iran_sites,value=True),
            BoolConfig(key=ConfigEnum.allow_invalid_sni,value=True),
            # BoolConfig(key=ConfigEnum.kcp_enable,value=False),
            # StrConfig(key=ConfigEnum.kcp_ports,value="88"),
            BoolConfig(key=ConfigEnum.auto_update,value=True),
            BoolConfig(key=ConfigEnum.speed_test,value=True),
            BoolConfig(key=ConfigEnum.only_ipv4,value=False),

            BoolConfig(key=ConfigEnum.vmess_enable,value=True),
            BoolConfig(key=ConfigEnum.http_proxy_enable,value=True),
            StrConfig(key=ConfigEnum.shared_secret,value=str(uuid.uuid4())),

            BoolConfig(key=ConfigEnum.telegram_enable,value=True),
            # StrConfig(key=ConfigEnum.telegram_secret,value=uuid.uuid4().hex),
            StrConfig(key=ConfigEnum.telegram_adtag,value=""),
            StrConfig(key=ConfigEnum.telegram_fakedomain, value="www.wikipedia.org"),
 
            BoolConfig(key=ConfigEnum.ssfaketls_enable,value=False),
            # StrConfig(key=ConfigEnum.ssfaketls_secret,value=str(uuid.uuid4())),
            StrConfig(key=ConfigEnum.ssfaketls_fakedomain, value="fa.wikipedia.org"),

            # BoolConfig(key=ConfigEnum.shadowtls_enable,value=False),
            # StrConfig(key=ConfigEnum.shadowtls_secret,value=str(uuid.uuid4())),
            # StrConfig(key=ConfigEnum.shadowtls_fakedomain, value="en.wikipedia.org"),

            # BoolConfig(key=ConfigEnum.ssr_enable,value=False),
            # # StrConfig(key=ConfigEnum.ssr_secret,value=str(uuid.uuid4())),
            # StrConfig(key=ConfigEnum.ssr_fakedomain, value="ar.wikipedia.org"),

            # BoolConfig(key=ConfigEnum.tuic_enable,value=False),
            # StrConfig(key=ConfigEnum.tuic_port,value=3048),

            BoolConfig(key=ConfigEnum.domain_fronting_tls_enable,value=False),
            BoolConfig(key=ConfigEnum.domain_fronting_http_enable,value=False),
            StrConfig(key=ConfigEnum.domain_fronting_domain,value=""),

            # BoolConfig(key=ConfigEnum.torrent_block,value=False),

            *get_proxy_rows_v1()
        ]

        # for c in ConfigEnum:
        #     if c in [d.key for d in data if type(d) in [BoolConfig,StrConfig]]:
        #         continue
        #     if c.type()==bool:
        #         data.append(BoolConfig(key=c,value=False))
        #     else:
        #         data.append(StrConfig(key=c,value=""))
                    

        
        db.session.bulk_save_objects(data)

def _v2():
    db.session.bulk_save_objects([
            StrConfig(key=ConfigEnum.telegram_lib,value="python"),
            StrConfig(key=ConfigEnum.admin_lang,value=hconfig(ConfigEnum.lang)),
        ])

def _v3():
        db.session.bulk_save_objects([
            StrConfig(key=ConfigEnum.branding_title,value=""),
            StrConfig(key=ConfigEnum.branding_site,value=""),
            StrConfig(key=ConfigEnum.branding_freetext,value=""),
            BoolConfig(key=ConfigEnum.v2ray_enable,value=False),
        ])

def _v6():
    try:
        Proxy.query.filter(Proxy.name=='tls XTLS direct trojan').delete()
        Proxy.query.filter(Proxy.name=='tls XTLSVision direct trojan').delete()
    except:
        pass
    db.session.bulk_save_objects([
        *make_proxy_rows(["XTLS direct vless"])
    ])

def _v8():
    db.session.bulk_save_objects([
        *make_proxy_rows([
        "grpc direct vless",
        "grpc direct trojan",
        "grpc direct vmess"])
    ])
def init_db():
    
    try:
        db.engine.execute('ALTER TABLE user ADD COLUMN monthly BOOLEAN')
        db.engine.execute('ALTER TABLE user RENAME COLUMN monthly_usage_limit_GB TO usage_limit_GB')       
    except:
        pass
    try:
        column_type = Domain.cdn_ip.type.compile(db.engine.dialect)
        db.engine.execute(f'ALTER TABLE domain ADD COLUMN cdn_ip {column_type}')
    except:
        pass
    
    db_version=int(hconfig(ConfigEnum.db_version) or 0) 
    print(f"Current DB version is {db_version}")

    db_actions={1:_v1,2:_v2,3:_v3,6:_v6,8:_v8}
    for ver,db_action in db_actions.items():
        if ver<=db_version:continue
        print(f"Updating db from version {db_version}")
        db_action()
        db.session.commit()
        print(f"Updated successfuly db from version {db_version} to {ver}")
        db_version=ver
        
    # 
    StrConfig.query.filter(StrConfig.key == ConfigEnum.db_version).update({'value': db_version})
    db.session.commit()
    return BoolConfig.query.all()




def get_proxy_rows_v1():
    return make_proxy_rows([   
        'WS Fake vless',
        'WS Fake trojan',
        'WS Fake vmess',
        # 'grpc Fake vless',
        # 'grpc Fake trojan',
        # 'grpc Fake vmess',
        # "XTLS direct vless",
        # "XTLS direct trojan",
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
        # "h1 direct vless",
        # "h1 direct vmess",
        "faketls direct ss",
        "WS direct v2ray",
        "shadowtls direct ss",
        "tcp direct ssr",
        "WS CDN v2ray"]
    )

def make_proxy_rows(cfgs):
    
    for l3 in ["tls", "http", "kcp"]:
        for c in cfgs:
            transport,cdn,proto=c.split(" ")
            if l3=="kcp" and cdn!="direct":
                continue
            if proto=="trojan" and l3 not in ["tls",'xtls']:
                continue
            if transport in ["grpc","XTLS","faketls"] and l3=="http":
                continue


            yield Proxy(l3=l3,transport=transport,cdn=cdn,proto=proto,enable=True,name=f'{l3} {c}')