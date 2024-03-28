from hiddifypanel.models import *
from hiddifypanel.database import db
from hiddifypanel import Events, hutils

commercial = False


def init_app(app):
    from .restapi import v1 as restapi_v1
    restapi_v1.init_app(app)
    from .restapi.v2 import admin as api_v2_admin
    from .restapi.v2 import user as api_v2_user
    from .restapi.v2 import parent as api_v2_parent
    from .restapi.v2 import child as api_v2_child
    from .restapi.v2 import panel as api_v2_panel
    api_v2_parent.init_app(app)
    api_v2_admin.init_app(app)
    api_v2_user.init_app(app)
    api_v2_child.init_app(app)
    api_v2_panel.init_app(app)
    return


def is_valid():
    return True


def config_changed_event(conf, old_value):
    if conf.key == ConfigEnum.is_parent:
        if conf.value and not is_valid():
            set_hconfig(ConfigEnum.is_parent, False)
        if not old_value and conf.value:
            Domain.query.delete()
            new_domain = hutils.network.get_ip_str(4) + ".sslip.io"
            if not ParentDomain.query.filter(ParentDomain.domain == new_domain).first():
                db.session.add(ParentDomain(domain=hutils.network.get_ip_str(4) + ".sslip.io"))
                db.session.commit()


Events.config_changed.subscribe(config_changed_event)


# def db_init_event(db_version):
#     # if not is_valid():
#     #     db.add(BoolConfig(ConfigEnum.db_version,10,child_id=0))
#     #     db.add(BoolConfig(ConfigEnum.db_version,11,child_id=0))
#     #     return
#     if hconfig(ConfigEnum.is_parent) and ParentDomain.query.count()==0:
#         external_ip=hiddify.get_ip(4)
#         db.session.add(ParentDomain(domain=f"{external_ip}.sslip.io",show_domains=[]))
# Events.db_init_event.subscribe(db_init_event)


def admin_prehook(flaskadmin, admin_bp):
    # from .ParentDomainAdmin import ParentDomainAdmin
    # flaskadmin.add_view(ParentDomainAdmin(ParentDomain, db.session))
    from .ProxyDetailsAdmin import ProxyDetailsAdmin
    flaskadmin.add_view(ProxyDetailsAdmin(Proxy, db.session))
    # CommercialSettings.register(admin_bp)


Events.admin_prehook.subscribe(admin_prehook)


# def db_prehook():
# flaskadmin.add_view(ParentDomainAdmin(ParentDomain, db.session))
# from . import ProxyDominAdmin
# CommercialSettings.register(admin_bp)

# Events.db_prehook.subscribe(db_prehook)
