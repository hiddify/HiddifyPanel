import click


from hiddifypanel.panel.database import db
from hiddifypanel.models import BoolConfig,StrConfig,ConfigEnum
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
    db.create_all()
    external_ip=urllib.request.urlopen('https://v4.ident.me/').read().decode('utf8')
    next10year = datetime.date.today() + relativedelta.relativedelta(years=10)
    data = [
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
    return BoolConfig.query.all()

def init_app(app):
    # add multiple commands in a bulk
    for command in [init_db, drop_db]:
        app.cli.add_command(app.cli.command()(command))

    
    @app.cli.command()
    @click.option("--admin_secret", "-a")
    def set_admin_secret(admin_secret):
        db.session.query(Config).filter(Config.key == ConfigEnum.admin_secret).update({'value': admin_secret})
        session.commit()
        return "success"

    @app.cli.command()
    @click.option("--domain", "-d")
    def add_domain(domain):
        db.session.query(Config).filter(Config.key == ConfigEnum.admin_secret).update({'value': admin_secret})
        data = [Domain(domain=domain,mode=DomainType.direct)]
        db.session.bulk_save_objects(data)
        session.commit()
        return "success"
