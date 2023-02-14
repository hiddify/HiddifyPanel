from flask import Blueprint,url_for,request,jsonify,g
from flask_admin import Admin
# from flask_sockets import Sockets

from .SettingAdmin import SettingAdmin 
from .DomainAdmin import DomainAdmin
from .ConfigAdmin import ConfigAdmin
from .ProxyAdmin import ProxyAdmin
from .Actions import Actions
from .Backup import Backup
from .QuickSetup import QuickSetup
from hiddifypanel.models import  StrConfig,ConfigEnum
# from .resources import ProductItemResource, ProductResource
from hiddifypanel.panel.database import db
from hiddifypanel.models import User,Domain,BoolConfig,StrConfig,Proxy,hconfig,ConfigEnum
from .Dashboard import Dashboard

from flask_admin.menu import MenuLink

import uuid
from flask_adminlte3 import AdminLTE3
flask = Blueprint("flask", __name__, url_prefix=f"/<proxy_path>/<user_secret>/",template_folder="templates")
bp = Blueprint("admin", __name__, url_prefix=f"/<proxy_path>/<user_secret>/admin/",template_folder="templates")

# from extensions import socketio


def init_app(app):
    
    from .UserAdmin import UserAdmin
    # admin_secret=StrConfig.query.filter(StrConfig.key==ConfigEnum.admin_secret).first()
    # 
    # return
    # admin = Admin(endpoint="admin",index_view=Dashboard(),base_template='lte-master.html',static_url_path="/static/")    
    
    admin = Admin(endpoint="admin",base_template='flaskadmin-layout.html')    

    admin.template_mode = "bootstrap4"
    
    

    
    # admin.init_app(app)
    
    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(DomainAdmin(Domain, db.session))
    
    
    
    admin.init_app(flask)
    adminlte=AdminLTE3()
    adminlte.init_app(app)
    SettingAdmin.register(bp)
    ProxyAdmin.register(bp)
    Actions.register(bp)
    QuickSetup.register(bp)
    Backup.register(bp)
    Dashboard.register(bp,route_base="/")

    
    # bp.add_url_rule('/admin/quicksetup/',endpoint="quicksetup",view_func=QuickSetup.index,methods=["GET"])
    # bp.add_url_rule('/admin/quicksetup/',endpoint="quicksetup-save", view_func=QuickSetup.save,methods=["POST"])


    app.register_blueprint(bp)
    app.register_blueprint(flask)
    app.add_url_rule("/<proxy_path>/<user_secret>/admin/static/<filename>/",endpoint="admin.static")# fix bug in admin with blueprint
    
    # sockets = Sockets(app)
    # sockets.register_blueprint(bp)

    # print(app.url_map)    
    
