from flask import Blueprint,url_for,request,jsonify,g
from flask_admin import Admin

from . import FullConfigAdmin 
from .DomainAdmin import DomainAdmin
from .ConfigAdmin import ConfigAdmin
# from .ProxyAdmin import ProxyAdmin
from . import QuickSetup,ProxyAdmin
from hiddifypanel.models import  StrConfig,ConfigEnum
# from .resources import ProductItemResource, ProductResource
from hiddifypanel.panel.database import db
from hiddifypanel.models import User,Domain,BoolConfig,StrConfig,Proxy
from .dashboard import Dashboard

from flask_admin.menu import MenuLink
from . import actions 
import uuid
from flask_adminlte3 import AdminLTE3
bp = Blueprint("admin", __name__, url_prefix=f"/<proxy_path>/<user_secret>/",template_folder="templates")



def init_app(app):
    from .UserAdmin import UserAdmin
    # admin_secret=StrConfig.query.filter(StrConfig.key==ConfigEnum.admin_secret).first()
    # 
    # return
    # admin = Admin(endpoint="admin",index_view=Dashboard(),base_template='lte-master.html',static_url_path="/static/")    
    
    admin = Admin(endpoint="admin",index_view=Dashboard(),base_template='flaskadmin-layout.html')    

    admin.template_mode = app.config.FLASK_ADMIN_TEMPLATE_MODE
    
    

    
    # admin.init_app(app)
    
    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(DomainAdmin(Domain, db.session))
    # admin.add_view(ProxyAdmin(Proxy, db.session))
    # admin.add_view(ConfigAdmin(BoolConfig, db.session))
    # admin.add_view(ConfigAdmin(StrConfig, db.session))
    # admin.add_view(Actions(name="Dashboard",endpoint="home",url="/<proxy_path>/<user_secret>/admin/",))
    # admin.add_view(Actions(name="Actions",endpoint="actions",))
    
    # admin.add_link(MenuLink(name='Apply Changes', category='', url=f"/{g.proxy_path}/{g.user_secret}/actions/apply_configs"))
    # admin.
    admin.init_app(bp)
    adminlte=AdminLTE3()
    adminlte.init_app(app)
    bp.add_url_rule('/admin/config/getallbabel/',view_func=FullConfigAdmin.get_babel_string,methods=["GET"])
    bp.add_url_rule('/admin/config/',endpoint="config",view_func=FullConfigAdmin.index,methods=["GET"])
    bp.add_url_rule('/admin/config/',endpoint="config-save",view_func=FullConfigAdmin.save,methods=["POST"])
    bp.add_url_rule('/admin/proxy/',endpoint="proxy",view_func=ProxyAdmin.index,methods=["GET"])
    bp.add_url_rule('/admin/proxy/',endpoint="proxy-save",view_func=ProxyAdmin.save,methods=["POST"])

    bp.add_url_rule('/admin/quicksetup/',endpoint="quicksetup",view_func=QuickSetup.index,methods=["GET"])
    bp.add_url_rule('/admin/quicksetup/',endpoint="quicksetup-save", view_func=QuickSetup.save,methods=["POST"])

    import flask_babelex

    actions_bp = Blueprint("actions", __name__, url_prefix=f"/actions/",template_folder="templates")    
    actions.register_routes(actions_bp)
    
    bp.register_blueprint(actions_bp)
    app.register_blueprint(bp)
    app.add_url_rule("/<proxy_path>/<user_secret>/admin/static/<filename>/",endpoint="admin.static")# fix bug in admin with blueprint
    # app.add_url_rule("/<proxy_path>/<user_secret>/admin/static/<filename>",endpoint="admin.admin.static")# fix bug in admin with blueprint
    # app.add_url_rule("/<proxy_path>/<user_secret>/admin/static/<filename>",endpoint="adminlte.static")# fix bug in admin with blueprint
    print(app.url_map)    
    
