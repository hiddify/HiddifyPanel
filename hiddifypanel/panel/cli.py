import click


from hiddifypanel.panel.database import db
from hiddifypanel.models import BoolConfig,StrConfig,ConfigEnum,hconfig,Proxy
from hiddifypanel.models import Domain,DomainType
from hiddifypanel.models import User
from hiddifypanel.panel import hiddify
import random
import uuid
import urllib
import string


def drop_db():
    """Cleans database"""
    db.drop_all()



def get_random_string():
    # With combination of lower and upper case
    length=random.randint(10, 30)
    characters = string.ascii_letters + string.digits
    result_str = ''.join(random.choice(characters) for i in range(length))
    return result_str

from dateutil import relativedelta
import datetime


def init_db():
    
    
    
    db_version=hconfig(ConfigEnum.db_version)
    if db_version==None:
        
        db.create_all()
        next10year = datetime.date.today() + relativedelta.relativedelta(years=10)
        external_ip=urllib.request.urlopen('https://v4.ident.me/').read().decode('utf8')
        
        data = [
            StrConfig(key=ConfigEnum.db_version,value=1),
            User(name="default",monthly_usage_limit_GB=9000,expiry_time=next10year),
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
            StrConfig(key=ConfigEnum.telegram_fakedomain, value="www.wikipedia.org"),

            BoolConfig(key=ConfigEnum.ssfaketls_enable,value=False),
            # StrConfig(key=ConfigEnum.ssfaketls_secret,value=str(uuid.uuid4())),
            StrConfig(key=ConfigEnum.ssfaketls_fakedomain, value="fa.wikipedia.org"),

            BoolConfig(key=ConfigEnum.shadowtls_enable,value=False),
            # StrConfig(key=ConfigEnum.shadowtls_secret,value=str(uuid.uuid4())),
            StrConfig(key=ConfigEnum.shadowtls_fakedomain, value="en.wikipedia.org"),

            BoolConfig(key=ConfigEnum.ssr_enable,value=False),
            # StrConfig(key=ConfigEnum.ssr_secret,value=str(uuid.uuid4())),
            StrConfig(key=ConfigEnum.ssr_fakedomain, value="ar.wikipedia.org"),

            BoolConfig(key=ConfigEnum.tuic_enable,value=False),
            StrConfig(key=ConfigEnum.tuic_port,value=3048),

            BoolConfig(key=ConfigEnum.domain_fronting_tls_enable,value=False),
            BoolConfig(key=ConfigEnum.domain_fronting_http_enable,value=False),
            StrConfig(key=ConfigEnum.domain_fronting_domain,value=""),
            *get_proxy_rows()
        ]

        
        db.session.bulk_save_objects(data)
        db.session.commit()
        db_version=1
    
    if db_version==1:
        pass # for next update

    return BoolConfig.query.all()

def all_configs():
    import json
    print(json.dumps(hiddify.all_configs()))

def update_usage():
    print(hiddify.update_usage())

def test():
    print(ConfigEnum("auto_update1"))

def admin_links():
        proxy_path=hconfig(ConfigEnum.proxy_path)
        admin_secret=hconfig(ConfigEnum.admin_secret)
        
        admin_links=f"Not Secure:\n   http://{server_ip}/{proxy_path}/{admin_secret}/admin/\n"
        domains=[d.domain for d in Domain.query.all()]
        admin_links+=f"Secure:\n"
        # domains=[*domains,f'{server_ip}.sslip.io']
        for d in domains:
            admin_links+=f"   https://{d}/{proxy_path}/{admin_secret}/admin/\n"

        print(admin_links)
def admin_path():
        proxy_path=hconfig(ConfigEnum.proxy_path)
        admin_secret=hconfig(ConfigEnum.admin_secret)        
        print(f"/{proxy_path}/{admin_secret}/admin/")

def init_app(app):
    # add multiple commands in a bulk
    #print(app.config['SQLALCHEMY_DATABASE_URI'] )
    for command in [init_db, drop_db, all_configs,update_usage,test,admin_links,admin_path]:
        app.cli.add_command(app.cli.command()(command))

    @app.cli.command()
    @click.option("--domain", "-d")
    def add_domain(domain):
        if Domain.query.filter(Domain.domain==domain).first():
            return "Domain already exist."    

        data = [Domain(domain=domain,mode=DomainType.direct)]
        db.session.bulk_save_objects(data)
        db.session.commit()
        return "success"
        
    @app.cli.command()
    @click.option("--admin_secret", "-a")
    def set_admin_secret(admin_secret):
        StrConfig.query.filter(StrConfig.key == ConfigEnum.admin_secret).update({'value': admin_secret})
        db.session.commit()
        return "success"

    @app.cli.command()
    @click.option("--config", "-c")
    def import_config(config):
        next10year = datetime.date.today() + relativedelta.relativedelta(years=10)
        data=[]
        if "USER_SECRET" in config:
            secrets=config["USER_SECRET"].split(";")
            for i,s in enumerate(secrets):
                data.append(User(name=f"default {i}",uuid=uuid.UUID(s),monthly_usage_limit_GB=9000,expiry_time=next10year))

        if "MAIN_DOMAIN" in config:
            domains=config["MAIN_DOMAIN"].split(";")
            for i,d in enumerate(domains):
                if not Domain.query.filter(Domain.domain==d).first():
                    data.append(Domain(domain=d,mode=DomainType.direct),)
        
        strmap={
            "TELEGRAM_FAKE_TLS_DOMAIN": ConfigEnum.telegram_fakedomain,
            "TELEGRAM_SECRET":ConfigEnum.shared_secret,
            "SS_FAKE_TLS_DOMAIN":ConfigEnum.ssfaketls_fakedomain,
            "FAKE_CDN_DOMAIN":ConfigEnum.domain_fronting_domain,
            "BASE_PROXY_PATH":ConfigEnum.proxy_path,
            "ADMIN_SECRET":ConfigEnum.admin_secret,
            "TELEGRAM_AD_TAG":ConfigEnum.telegram_adtag
        }
        boolmap={
        "ENABLE_SS":ConfigEnum.ssfaketls_enable,
        "ENABLE_TELEGRAM":ConfigEnum.telegram_enable,
        "ENABLE_VMESS":ConfigEnum.vmess_enable,
        # "ENABLE_MONITORING":ConfigEnum.ssfaketls_enable,
        "ENABLE_FIREWALL":ConfigEnum.firewall,
        "ENABLE_NETDATA":ConfigEnum.netdata,
        "ENABLE_HTTP_PROXY":ConfigEnum.http_proxy_enable,
        "ALLOW_ALL_SNI_TO_USE_PROXY":ConfigEnum.allow_invalid_sni,
        "ENABLE_AUTO_UPDATE":ConfigEnum.auto_update,
        "ENABLE_SPEED_TEST":ConfigEnum.speed_test,
        "BLOCK_IR_SITES":ConfigEnum.block_iran_sites,
        "ONLY_IPV4":ConfigEnum.only_ipv4
        }

        for k in config:
            if k in strmap:
                if hconfig(strmap[k]) is None:
                    data.append(StrConfig(key=strmap[k],value=config[k]))
                else:    
                    StrConfig.query.filter(StrConfig.key==strmap[k]).update({
                        'value':config[k]
                    })
            if k in boolmap:
                if hconfig(boolmap[k]) is None:
                    data.append(BoolConfig(key=boolmap[k],value=config[k]))
                else:    
                    BoolConfig.query.filter(BoolConfig.key==strmap[k]).update({
                        'value':config[k]
                    })
        if len(data):
            db.session.bulk_save_objects(data)
        db.session.commit()


def get_proxy_rows():
    cfgs=[   
        'WS Fake vless',
        'WS Fake trojan',
        'WS Fake vmess',
        # 'grpc Fake vless',
        # 'grpc Fake trojan',
        # 'grpc Fake vmess',
        # "XTLS direct vless",
        "XTLS direct trojan",
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
        "ws direct v2ray",
        "shadowtls direct ss",
        "tcp direct ssr",
        "ws CDN v2ray"]
    for l3 in ["tls", "http", "kcp"]:
        for c in cfgs:
            transport,cdn,proto=c.split(" ")
            if l3=="kcp" and cdn!="direct":
                continue
            if proto=="trojan" and l3!="tls":
                continue
            if transport in ["XTLS","faketls"] and l3=="http":
                continue


            yield Proxy(l3=l3,transport=transport,cdn=cdn,proto=proto,enable=True,name=f'{l3} {c}')