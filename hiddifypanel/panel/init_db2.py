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
def _v1():
        
        next10year = datetime.date.today() + relativedelta.relativedelta(years=6)
        external_ip=hiddify.get_ip(4)
        rnd_domains=get_random_domains(5)
        data = [
            StrConfig(key=ConfigEnum.db_version,value=1),
            User(name="default",usage_limit_GB=3000,package_days=3650,mode=UserMode.weekly),
            Domain(domain=external_ip+".sslip.io",mode=DomainType.direct),
            StrConfig(key=ConfigEnum.admin_secret,value=str(uuid.uuid4())),
            StrConfig(key=ConfigEnum.http_ports,value="80"),
            StrConfig(key=ConfigEnum.tls_ports,value="443"),
            
            StrConfig(key=ConfigEnum.decoy_domain,value=rnd_domains[0]),
            StrConfig(key=ConfigEnum.proxy_path,value=get_random_string()),
            BoolConfig(key=ConfigEnum.firewall,value=True),
            BoolConfig(key=ConfigEnum.netdata,value=True),
            StrConfig(key=ConfigEnum.lang,value='fa'),
            
            BoolConfig(key=ConfigEnum.block_iran_sites,value=True),
            BoolConfig(key=ConfigEnum.allow_invalid_sni,value=True),
            BoolConfig(key=ConfigEnum.kcp_enable,value=False),
            StrConfig(key=ConfigEnum.kcp_ports,value="88"),
            BoolConfig(key=ConfigEnum.auto_update,value=True),
            BoolConfig(key=ConfigEnum.speed_test,value=True),
            BoolConfig(key=ConfigEnum.only_ipv4,value=False),

            BoolConfig(key=ConfigEnum.vmess_enable,value=True),
            BoolConfig(key=ConfigEnum.http_proxy_enable,value=True),
            StrConfig(key=ConfigEnum.shared_secret,value=str(uuid.uuid4())),

            BoolConfig(key=ConfigEnum.telegram_enable,value=True),
            # StrConfig(key=ConfigEnum.telegram_secret,value=uuid.uuid4().hex),
            StrConfig(key=ConfigEnum.telegram_adtag,value=""),
            StrConfig(key=ConfigEnum.telegram_fakedomain, value=rnd_domains[1]),
 
            BoolConfig(key=ConfigEnum.ssfaketls_enable,value=False),
            # StrConfig(key=ConfigEnum.ssfaketls_secret,value=str(uuid.uuid4())),
            StrConfig(key=ConfigEnum.ssfaketls_fakedomain, value=rnd_domains[2]),

            BoolConfig(key=ConfigEnum.shadowtls_enable,value=False),
            # StrConfig(key=ConfigEnum.shadowtls_secret,value=str(uuid.uuid4())),
            StrConfig(key=ConfigEnum.shadowtls_fakedomain, value=rnd_domains[3]),

            BoolConfig(key=ConfigEnum.ssr_enable,value=False),
            # StrConfig(key=ConfigEnum.ssr_secret,value=str(uuid.uuid4())),
            StrConfig(key=ConfigEnum.ssr_fakedomain, value=rnd_domains[4]),

            BoolConfig(key=ConfigEnum.tuic_enable,value=False),
            StrConfig(key=ConfigEnum.tuic_port,value=3048),

            BoolConfig(key=ConfigEnum.domain_fronting_tls_enable,value=False),
            BoolConfig(key=ConfigEnum.domain_fronting_http_enable,value=False),
            StrConfig(key=ConfigEnum.domain_fronting_domain,value=""),

            # BoolConfig(key=ConfigEnum.torrent_block,value=False),

            *get_proxy_rows_v1()
        ]
        fake_domains=['speedtest.net']
        for fd in fake_domains:
            if not Domain.query.filter(Domain.domain==fd).first():
                db.session.add(Domain(domain=fd,mode='fake',alias='fake domain',cdn_ip=external_ip))
        # for c in ConfigEnum:
        #     if c in [d.key for d in data if type(d) in [BoolConfig,StrConfig]]:
        #         continue
        #     if c.type()==bool:
        #         data.append(BoolConfig(key=c,value=False))
        #     else:
        #         data.append(StrConfig(key=c,value=""))
                    

        
        db.session.bulk_save_objects(data)

def _v2():
    add_config_if_not_exist(ConfigEnum.telegram_lib, "python")
    add_config_if_not_exist(ConfigEnum.admin_lang, hconfig(ConfigEnum.lang))

def _v3():
    add_config_if_not_exist(ConfigEnum.branding_title, "")
    add_config_if_not_exist(ConfigEnum.branding_site, "")
    add_config_if_not_exist(ConfigEnum.branding_freetext, "")
    add_config_if_not_exist(ConfigEnum.v2ray_enable, False)
        

def _v6():
    try:
        Proxy.query.filter(Proxy.name=='tls XTLS direct trojan').delete()
        Proxy.query.filter(Proxy.name=='tls XTLSVision direct trojan').delete()
    except:
        pass
    # db.session.bulk_save_objects([
    #     *make_proxy_rows(["XTLS direct vless"])
    # ])


def _v9():
    try:
        add_column(User.mode)
        add_column(User.comment)
        for u in User.query.all():
            u.mode= UserMode.monthly if u.monthly else UserMode.no_reset
    except:
        pass
    
    add_config_if_not_exist(ConfigEnum.is_parent, False)
    add_config_if_not_exist(ConfigEnum.parent_panel, '')
    add_config_if_not_exist(ConfigEnum.unique_id,str(uuid.uuid4()))

def _v10():
    all_configs=get_hconfigs()
    try:        
        db.engine.execute("ALTER TABLE `str_config` RENAME TO `str_config_old`")
        db.engine.execute("ALTER TABLE `bool_config` RENAME TO `bool_config_old`")
    except:
        pass
    db.create_all()
    
    rows=[]
    
    for c,v in all_configs.items():
        if c.type()==bool:
            rows.append(BoolConfig(key=c,value=v,child_id=0))
        else:
            rows.append(StrConfig(key=c,value=v,child_id=0))
    
    db.session.bulk_save_objects(rows)
    




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
        "tcp direct ssr",
        "WS CDN v2ray"]
    )

def make_proxy_rows(cfgs):
    
    for l3 in ["tls_h2","tls", "http", "kcp"]:
        for c in cfgs:
            transport,cdn,proto=c.split(" ")
            if l3=="kcp" and cdn!="direct":
                continue
            if proto=="trojan" and l3 not in ["tls",'xtls','tls_h2']:
                continue
            if transport in ["grpc","XTLS","faketls"] and l3=="http":
                continue
            # if l3 == "tls_h2" and transport =="grpc":
            #     continue
            enable=l3!="http" or proto=="vmess"
            if not Proxy.query.filter(Proxy.l3==l3,Proxy.transport==transport,Proxy.cdn==cdn,Proxy.proto==proto).first():
                yield Proxy(l3=l3,transport=transport,cdn=cdn,proto=proto,enable=enable,name=f'{l3} {c}')


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


def get_random_string(min_=10,max_=30):
    # With combination of lower and upper case
    length=random.randint(min_, max_)
    characters = string.ascii_letters + string.digits
    result_str = ''.join(random.choice(characters) for i in range(length))
    return result_str

def get_random_domains(count=1,retry=3):
    try:
        irurl="https://api.ooni.io/api/v1/measurements?probe_cc=IR&test_name=web_connectivity&anomaly=false&confirmed=false&failure=false&order_by=test_start_time&limit=1000"
        # cnurl="https://api.ooni.io/api/v1/measurements?probe_cc=CN&test_name=web_connectivity&anomaly=false&confirmed=false&failure=false&order_by=test_start_time&limit=1000"
        import requests
        data_ir=requests.get(irurl).json()
        # data_cn=requests.get(url).json()
        from urllib.parse import urlparse
        domains=[urlparse(d['input']).netloc.lower() for d in data_ir['results'] if d['scores']['blocking_country']==0.0]
        domains=[d for d in domains if not d.endswith(".ir")]
        
        return random.sample(domains, count)
    except Exception as e:
        print('Error, getting random domains... ',e,'retrying...',retry)
        if retry<=0:
            defdomains=["fa.wikipedia.org",'en.wikipedia.org','wikipedia.org','yahoo.com','en.yahoo.com']
            print('Error, using default domains')
            return random.sample(defdomains, count)
        return get_random_domains(count,retry-1)

