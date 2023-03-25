
from .parent_domain import ParentDomain
from .ParentDomainAdmin import ParentDomainAdmin
from .ProxyDetailsAdmin import ProxyDetailsAdmin
from .CommercialSettings import CommercialSettings
from . import utils
from hiddifypanel.models import  *
from hiddifypanel.panel.database import db
from hiddifypanel import Events
from .utils import is_valid
commercial=False
def init_app(app):
    @app.url_value_preprocessor
    def pull_secret_code(endpoint, values):
        if not is_valid():
            abort(400, "i"+"n"+"v"+"a"+"l"+"i"+"d"+" "+"r"+"e"+"q"+"u"+"e"+"s"+"t")
    with app.app_context():
        if not hconfig(ConfigEnum.license):return
        
    # return 
    
    


def config_changed_event(conf,old_value):
    

    if conf.key==ConfigEnum.is_parent:
        if conf.value and not is_valid():
            set_hconfig(ConfigEnum.is_parent,False)
        if not old_value and conf.value:
            Domain.query.delete()
            db.session.commit()
            db.session.add(ParentDomain(domain=hiddify.get_ip(4)+".sslip.io"))
            db.session.commit()

Events.config_changed.subscribe(config_changed_event)



def db_init_event(db_version):
    if not is_valid():
        db.add(BoolConfig(ConfigEnum.db_version,10,child_id=0))
        db.add(BoolConfig(ConfigEnum.db_version,11,child_id=0))
        return
    # if hconfig(ConfigEnum.is_parent) and ParentDomain.query.count()==0:
    #     external_ip=hiddify.get_ip(4)
    #     db.session.add(ParentDomain(domain=f"{external_ip}.sslip.io",show_domains=[]))
Events.db_init_event.subscribe(db_init_event)



def admin_prehook(flaskadmin,admin_bp):
    flaskadmin.add_view(ParentDomainAdmin(ParentDomain, db.session))
    flaskadmin.add_view(ProxyDetailsAdmin(Proxy, db.session))
    CommercialSettings.register(admin_bp)

Events.admin_prehook.subscribe(admin_prehook)