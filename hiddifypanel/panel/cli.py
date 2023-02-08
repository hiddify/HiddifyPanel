import click


from hiddifypanel.panel.database import db
from hiddifypanel.panel.init_db import init_db
from hiddifypanel.models import BoolConfig,StrConfig,ConfigEnum,hconfig,Proxy
from hiddifypanel.models import Domain,DomainType
from hiddifypanel.models import User
from hiddifypanel.panel import hiddify
import random
import uuid
import urllib
import string
from dateutil import relativedelta
import datetime

def drop_db():
    """Cleans database"""
    db.drop_all()







def all_configs():
    import json
    configs=hiddify.all_configs()
    configs['hconfigs']['first_setup']=len(configs['domains'])==1 and 'sslip.io' in configs['domains'][0]['domain'] and len(configs['users'])==1 and configs['users'][0]['name']=="default"
    # configs

    print(json.dumps(configs))

def update_usage():
    print(hiddify.update_usage())

def test():
    print(ConfigEnum("auto_update1"))

def admin_links():
        proxy_path=hconfig(ConfigEnum.proxy_path)
        admin_secret=hconfig(ConfigEnum.admin_secret)
        server_ip=hiddify.get_ip(4)
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
                data.append(User(name=f"default {i}",uuid=uuid.UUID(s),usage_limit_GB=9000,expiry_time=next10year))

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

