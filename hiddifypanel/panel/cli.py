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
            StrConfig(category="hidden",key=ConfigEnum.db_version,value=1),
            User(name="default",monthly_usage_limit_GB=9000,expiry_time=next10year),
            Domain(domain=external_ip+".sslip.io",mode=DomainType.direct),
            StrConfig(category="admin",key=ConfigEnum.admin_secret,value=str(uuid.uuid4())),
            StrConfig(category="ports",key=ConfigEnum.http_ports,value="80"),
            StrConfig(category="ports",key=ConfigEnum.tls_ports,value="443"),
            
            StrConfig(category="general",key=ConfigEnum.decoy_site,value="https://www.wikipedia.org/"),
            StrConfig(category="proxies",key=ConfigEnum.proxy_path,value=get_random_string()),
            BoolConfig(category="general",key=ConfigEnum.firewall,value=False),
            BoolConfig(category="general",key=ConfigEnum.netdata,value=True),
            StrConfig(category="general",key=ConfigEnum.lang,value='en'),
            
            BoolConfig(category="proxies",key=ConfigEnum.block_iran_sites,value=True),
            BoolConfig(category="proxies",key=ConfigEnum.allow_invalid_sni,value=True),
            BoolConfig(category="kcp",key=ConfigEnum.kcp_enable,value=False),
            StrConfig(category="kcp",key=ConfigEnum.kcp_ports,value="88"),
            BoolConfig(category="general",key=ConfigEnum.auto_update,value=True),
            BoolConfig(category="general",key=ConfigEnum.speed_test,value=True),
            BoolConfig(category="general",key=ConfigEnum.only_ipv4,value=True),

            BoolConfig(category="proxies",key=ConfigEnum.vmess_enable,value=True),
            BoolConfig(category="ports",key=ConfigEnum.http_proxy_enable,value=True),
            StrConfig(category="proxies",key=ConfigEnum.shared_secret,value=str(uuid.uuid4())),

            BoolConfig(category="telegram",key=ConfigEnum.telegram_enable,value=True),
            # StrConfig(category="telegram",key=ConfigEnum.telegram_secret,value=uuid.uuid4().hex),
            StrConfig(category="telegram",key=ConfigEnum.telegram_adtag,value=""),
            StrConfig(category="telegram",key=ConfigEnum.telegram_fakedomain, value="www.wikipedia.org"),

            BoolConfig(category="ssfaketls",key=ConfigEnum.ssfaketls_enable,value=False),
            # StrConfig(category="ssfaketls",key=ConfigEnum.ssfaketls_secret,value=str(uuid.uuid4())),
            StrConfig(category="ssfaketls",key=ConfigEnum.ssfaketls_fakedomain, value="fa.wikipedia.org"),

            BoolConfig(category="shadowtls",key=ConfigEnum.shadowtls_enable,value=False),
            # StrConfig(category="shadowtls",key=ConfigEnum.shadowtls_secret,value=str(uuid.uuid4())),
            StrConfig(category="shadowtls",key=ConfigEnum.shadowtls_fakedomain, value="en.wikipedia.org"),

            BoolConfig(category="ssr",key=ConfigEnum.ssr_enable,value=False),
            # StrConfig(category="ssr",key=ConfigEnum.ssr_secret,value=str(uuid.uuid4())),
            StrConfig(category="ssr",key=ConfigEnum.ssr_fakedomain, value="en.wikipedia.org"),

            BoolConfig(category="tuic",key=ConfigEnum.tuic_enable,value=False),
            StrConfig(category="tuic",key=ConfigEnum.tuic_port,value=3048),

            BoolConfig(category="domain_fronting",key=ConfigEnum.domain_fronting_tls_enable,value=False),
            BoolConfig(category="domain_fronting",key=ConfigEnum.domain_fronting_http_enable,value=False),
            StrConfig(category="domain_fronting",key=ConfigEnum.domain_fronting_domain,value=""),
            *get_proxy_rows()
        ]

        
        db.session.bulk_save_objects(data)
        db.session.commit()
        db_version=1
    
    if db_version==1:
        pass # for next update

    return BoolConfig.query.all()

def all_configs():
    print(hiddify.all_configs())    

def update_usage():
    print(hiddify.update_usage())
def init_app(app):
    # add multiple commands in a bulk
    #print(app.config['SQLALCHEMY_DATABASE_URI'] )
    for command in [init_db, drop_db, all_configs,update_usage]:
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
            "TELEGRAM_SECRET":ConfigEnum.telegram_secret,
            "SS_FAKE_TLS_DOMAIN":ConfigEnum.ssfaketls_fakedomain,
            "FAKE_CDN_DOMAIN":ConfigEnum.fake_cdn_domain,
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