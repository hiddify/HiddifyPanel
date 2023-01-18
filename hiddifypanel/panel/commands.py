import click


from hiddifypanel.panel.database import db
from hiddifypanel.models import Config,ConfigEnum
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

def init_db():
    db.create_all()
    external_ip=urllib.request.urlopen('https://v4.ident.me/').read().decode('utf8')
    data = [
        Domain(domain=external_ip+".sslip.io",mode=DomainType.direct),
        Config(key=ConfigEnum.admin_secret,value=uuid.uuid4().hex),
        Config(key=ConfigEnum.tls_ports,value="443"),
        Config(key=ConfigEnum.http_ports,value="80"),
        Config(key=ConfigEnum.decoy_site,value="https://video-vcdn.varzesh3.com/"),
        Config(key=ConfigEnum.proxy_path,value=get_random_string()),
        Config(key=ConfigEnum.firewall,boolval=False),
        Config(key=ConfigEnum.netdata,boolval=True),
        Config(key=ConfigEnum.http_proxy,boolval=True),
        Config(key=ConfigEnum.iran_sites,value="block"),
        Config(key=ConfigEnum.allow_invalid_sni,boolval=True),
        Config(key=ConfigEnum.auto_update,boolval=True),
        Config(key=ConfigEnum.speed_test,boolval=True),
        Config(key=ConfigEnum.only_ipv4,boolval=True),
        
        
        Config(key=ConfigEnum.telegram_enable,boolval=True),
        Config(key=ConfigEnum.telegram_secret,value=uuid.uuid4().hex),
        Config(key=ConfigEnum.telegram_adtag,value=""),
        Domain(domain="video-vcdn.varzesh3.com",mode=DomainType.telegram_faketls),

        Config(key=ConfigEnum.ssfaketls_enable,boolval=False),
        Config(key=ConfigEnum.ssfaketls_secret,value=uuid.uuid4().hex),
        Domain(domain="video.varzesh3.com",mode=DomainType.ss_faketls),

    ]
    db.session.bulk_save_objects(data)
    db.session.commit()
    return Config.query.all()

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
