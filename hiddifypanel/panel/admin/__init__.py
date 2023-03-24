from flask import Blueprint,url_for,request,jsonify,g,redirect
from flask_admin import Admin
# from flask_sockets import Sockets

from .SettingAdmin import SettingAdmin 
from .DomainAdmin import DomainAdmin
from .ConfigAdmin import ConfigAdmin

from .ProxyAdmin import ProxyAdmin
from .ProxyDetailsAdmin import ProxyDetailsAdmin
from .Actions import Actions
from .Backup import Backup
from .QuickSetup import QuickSetup
from hiddifypanel.models import  StrConfig,ConfigEnum
# from .resources import ProductItemResource, ProductResource
from hiddifypanel.panel.database import db
from hiddifypanel.models import *
from .Dashboard import Dashboard

from flask_admin.menu import MenuLink

import uuid
from flask_adminlte3 import AdminLTE3
flask_bp = Blueprint("flask", __name__, url_prefix=f"/<proxy_path>/<user_secret>/",template_folder="templates")
admin_bp = Blueprint("admin", __name__, url_prefix=f"/<proxy_path>/<user_secret>/admin/",template_folder="templates")

# from extensions import socketio


def init_app(app):
    
    from .UserAdmin import UserAdmin
    # admin_secret=StrConfig.query.filter(StrConfig.key==ConfigEnum.admin_secret).first()
    # 
    # return
    # admin = Admin(endpoint="admin",index_view=Dashboard(),base_template='lte-master.html',static_url_path="/static/")    
    
    admin = Admin(endpoint="admin",base_template='flaskadmin-layout.html')    

    admin.template_mode = "bootstrap4"
    
    @app.route('/<proxy_path>/<user_secret>/admin')
    def auto_route():
        return redirect(request.url.replace("http://","https://")+"/")

    
    # admin.init_app(app)
    
    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(DomainAdmin(Domain, db.session))
    admin.add_view(ProxyDetailsAdmin(Proxy, db.session))
    
    
    
    
    admin.init_app(flask_bp)
    adminlte=AdminLTE3()
    adminlte.init_app(app)
    SettingAdmin.register(admin_bp)
    ProxyAdmin.register(admin_bp)
    Actions.register(admin_bp)
    QuickSetup.register(admin_bp)
    Backup.register(admin_bp)
    Dashboard.register(admin_bp,route_base="/")

    
    # admin_bp.add_url_rule('/admin/quicksetup/',endpoint="quicksetup",view_func=QuickSetup.index,methods=["GET"])
    # admin_bp.add_url_rule('/admin/quicksetup/',endpoint="quicksetup-save", view_func=QuickSetup.save,methods=["POST"])


    app.register_blueprint(admin_bp)
    flask_bp.debug=True
    app.register_blueprint(flask_bp)
    app.add_url_rule("/<proxy_path>/<user_secret>/admin/static/<filename>/",endpoint="admin.static")# fix bug in admin with blueprint
    
    # sockets = Sockets(app)
    # sockets.register_blueprint(admin_bp)

    # print(app.url_map)    
    
