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

def init_db():
    db.create_all()   
    
    try:
        db.engine.execute(f'update proxy set transport="WS" where transport = "ws"')
        db.engine.execute(f'DELETE from proxy where transport = "h1"')
    except:
        pass
    if hconfig(ConfigEnum.license):
        add_column(ParentDomain.alias)
    add_column(User.start_date)
    add_column(User.package_days)
    add_column(Child.unique_id)
    add_column(Domain.alias)
    add_column(Domain.child_id)
    add_column(Proxy.child_id)
    add_column(BoolConfig.child_id)
    add_column(StrConfig.child_id)

    if len(Domain.query.all())!=0 and BoolConfig.query.count()==0:
        db.engine.execute(f'DROP TABLE bool_config')
        db.engine.execute(f'ALTER TABLE bool_config_old RENAME TO bool_config')
    if len(Domain.query.all())!=0 and StrConfig.query.count()==0:
        db.engine.execute(f'DROP TABLE str_config')
        db.engine.execute(f'ALTER TABLE str_config_old RENAME TO str_config')

    try:
        add_column(User.monthly)
        db.engine.execute('ALTER TABLE user RENAME COLUMN monthly_usage_limit_GB TO usage_limit_GB')       
    except:
        pass
    try:
        db.engine.execute(f'update str_config set child_id=0 where child_id is NULL')
        db.engine.execute(f'update bool_config set child_id=0 where child_id is NULL')
        db.engine.execute(f'update domain set child_id=0 where child_id is NULL')
        db.engine.execute(f'update proxy set child_id=0 where child_id is NULL')
    except:
        pass
    
    add_column(Domain.cdn_ip)
    db_version=int(hconfig(ConfigEnum.db_version) or 0) 
    start_version=db_version
    # print(f"Current DB version is {db_version}")
    if not Child.query.filter(Child.id==0).first():
        print(Child.query.filter(Child.id==0).first())
        db.session.add(Child(unique_id="self",id=0))
        db.session.commit()
    

    for ver in range(1,40):
        if ver<=db_version:continue
        
        db_action=sys.modules[__name__].__dict__.get(f'_v{ver}',None)
        if not db_action:continue
        if start_version==0 and ver==10:continue

        print(f"Updating db from version {db_version}")
        db_action()
        Events.db_init_event.notify(db_version=db_version)
        print(f"Updated successfuly db from version {db_version} to {ver}")
        
        db_version=ver
        db.session.commit()
        set_hconfig(ConfigEnum.db_version,db_version,commit=False)
    
    
    db.session.commit()
    return BoolConfig.query.all()

def _v25():
    add_config_if_not_exist(ConfigEnum.country, "ir")
    add_config_if_not_exist(ConfigEnum.parent_panel, "")
    add_config_if_not_exist(ConfigEnum.is_parent, False)
    add_config_if_not_exist(ConfigEnum.license, "")
    


def _v21():
    db.session.bulk_save_objects(get_proxy_rows_v1())


def _v20():
    if hconfig(ConfigEnum.domain_fronting_domain):
        fake_domains=[hconfig(ConfigEnum.domain_fronting_domain)]
        
        direct_domain=Domain.query.filter(Domain.mode in [DomainType.direct,DomainType.relay]).first()
        if direct_domain:
            direct_host=direct_domain.domain
        else:
            direct_host=hiddify.get_ip(4)

        for fd in fake_domains:
            if not Domain.query.filter(Domain.domain==fd).first():
                db.session.add(Domain(domain=fd,mode='fake',alias='moved from domain fronting',cdn_ip=direct_host))    

def _v19():
    set_hconfig(ConfigEnum.path_trojan,get_random_string(7,15))
    set_hconfig(ConfigEnum.path_vless,get_random_string(7,15))
    set_hconfig(ConfigEnum.path_vmess,get_random_string(7,15))
    set_hconfig(ConfigEnum.path_ss,get_random_string(7,15))
    set_hconfig(ConfigEnum.path_grpc,get_random_string(7,15))
    set_hconfig(ConfigEnum.path_tcp,get_random_string(7,15))
    set_hconfig(ConfigEnum.path_ws,get_random_string(7,15))
    

def _v17():
    for u in User.query.all():
        if u.expiry_time:
            if not u.package_days:
                if not u.last_reset_time:
                    u.package_days=(u.expiry_time-datetime.date.today()).days
                    u.start_date=datetime.date.today()
                else:
                    u.package_days=(u.expiry_time-u.last_reset_time).days
                    u.start_date=u.last_reset_time
            u.expiry_time=None
            
            

def _v16():
    
    add_config_if_not_exist(ConfigEnum.tuic_enable,False)
    add_config_if_not_exist(ConfigEnum.shadowtls_enable,False)
    add_config_if_not_exist(ConfigEnum.shadowtls_fakedomain,"en.wikipedia.org")


        

def _v14():
    add_config_if_not_exist(ConfigEnum.utls,"chrome")
    
def _v13():
    add_config_if_not_exist(ConfigEnum.telegram_bot_token,"")
    add_config_if_not_exist(ConfigEnum.package_mode,"release")

def _v12():
    db.engine.execute(f'drop TABLE child')
    db.create_all()
    db.session.add(Child(id=0,unique_id="default"))

def _v11():
    add_column(User.last_online)




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

