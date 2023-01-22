import click


from hiddifypanel.panel.database import db
from hiddifypanel.models import BoolConfig,StrConfig,ConfigEnum,hconfig
from hiddifypanel.models import Domain,DomainType
from hiddifypanel.models import User
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
            StrConfig(category="general",key=ConfigEnum.db_version,value=1,description="Admin Secret will be used for accessing admin panel"),
            User(name="default",monthly_usage_limit_GB=9000,expiry_time=next10year),
            Domain(domain=external_ip+".sslip.io",mode=DomainType.direct),
            StrConfig(category="admin",key=ConfigEnum.admin_secret,value=str(uuid.uuid4()),description="Admin Secret will be used for accessing admin panel"),
            StrConfig(category="ports",key=ConfigEnum.tls_ports,value="443",description="TCP port, Comma seperated. e.g., 80,90,443"),
            StrConfig(category="ports",key=ConfigEnum.http_ports,value="80",description="TCP port, Comma seperated. e.g., 80,90,443"),
            StrConfig(category="ports",key=ConfigEnum.kcp_ports,value="443",description="UDP port for KCP, Comma seperated. e.g., 80,90,443"),
            StrConfig(category="general",key=ConfigEnum.decoy_site,value="https://www.wikipedia.org/",description="Fake site: simulate a site when someone visit your domain. Please use a well known domain in your data center. For example, if you are in azure data center, microsoft.com is a good example"),
            StrConfig(category="general",key=ConfigEnum.proxy_path,value=get_random_string(),description="a radom path to secure proxies"),
            BoolConfig(category="general",key=ConfigEnum.firewall,value=False,description="Enable Firewall"),
            BoolConfig(category="general",key=ConfigEnum.netdata,value=True,description="Enable Netdata. May use your CPU but not too much"),
            
            BoolConfig(category="general",key=ConfigEnum.block_iran_sites,value=True,description="Block Iranian sites to prevent detection by the govenment (experimental). If there is a problem, please disable it."),
            BoolConfig(category="general",key=ConfigEnum.allow_invalid_sni,value=True,description="Allow invalid SNIs"),
            BoolConfig(category="general",key=ConfigEnum.auto_update,value=True,description="Enable Auto Update"),
            BoolConfig(category="general",key=ConfigEnum.speed_test,value=True,description="Enable Speed Test (May use your bandwidth)"),
            BoolConfig(category="general",key=ConfigEnum.only_ipv4,value=True,description="Disable IPv6"),

            BoolConfig(category="proxies",key=ConfigEnum.vmess_enable,value=True,description="Enable Vmess (not recommended)"),
            BoolConfig(category="proxies",key=ConfigEnum.http_proxy,value=True,description="Allow HTTP proxy (not secure)"),

            BoolConfig(category="telegram",key=ConfigEnum.telegram_enable,value=True),
            StrConfig(category="telegram",key=ConfigEnum.telegram_secret,value=uuid.uuid4().hex,description="UUID Secret for telegram."),
            StrConfig(category="telegram",key=ConfigEnum.telegram_adtag,value="",description="adtag for telegram."),
            Domain(domain="www.wikipedia.org",mode=DomainType.telegram_faketls),

            BoolConfig(category="ssfaketls",key=ConfigEnum.ssfaketls_enable,value=False),
            StrConfig(category="ssfaketls",key=ConfigEnum.ssfaketls_secret,value=str(uuid.uuid4()),description="UUID Secret for shadowsocks fake tls."),
            Domain(domain="fa.wikipedia.org",mode=DomainType.ss_faketls),
        ]
    
        db.session.bulk_save_objects(data)
        db.session.commit()
        db_version=1
    
    if db_version==1:
        pass # for next update

    return BoolConfig.query.all()


def init_app(app):
    # add multiple commands in a bulk
    #print(app.config['SQLALCHEMY_DATABASE_URI'] )
    for command in [init_db, drop_db]:
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
        
        if "FAKE_CDN_DOMAIN" in config:
            d=config["FAKE_CDN_DOMAIN"]
            data.append(Domain(domain=d,mode=DomainType.fake_cdn),)
        if "TELEGRAM_FAKE_TLS_DOMAIN" in config:
            d=config["TELEGRAM_FAKE_TLS_DOMAIN"]
            data.append(Domain(domain=d,mode=DomainType.telegram_faketls),)
        if "SS_FAKE_TLS_DOMAIN" in config:
            d=config["SS_FAKE_TLS_DOMAIN"]
            data.append(Domain(domain=d,mode=DomainType.ss_faketls),)
        
        strmap={
            "TELEGRAM_SECRET":ConfigEnum.telegram_secret,
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
        "ENABLE_HTTP_PROXY":ConfigEnum.http_proxy,
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



