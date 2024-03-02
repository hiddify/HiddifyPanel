from flask import render_template, request, redirect, g
from . import fix_flaskadmin_babel
import flask_admin
from flask_admin import Admin
from hiddifypanel import Events
from .DomainAdmin import DomainAdmin
from .AdminstratorAdmin import AdminstratorAdmin


from hiddifypanel.database import db
from hiddifypanel.models import *
from apiflask import APIBlueprint
from flask_adminlte3 import AdminLTE3


flask_bp = APIBlueprint("flask", __name__, template_folder="templates", enable_openapi=False)
admin_bp = APIBlueprint("admin", __name__, template_folder="templates", enable_openapi=False)

flaskadmin = Admin(endpoint="admin", base_template='flaskadmin-layout.html',
                   translations_path="/opt/hiddify-develop/hiddify-panel/src/hiddifypanel/translations/")


def init_app(app):

    from .UserAdmin import UserAdmin
    # admin_secret=StrConfig.query.filter(StrConfig.key==ConfigEnum.admin_secret).first()
    #
    # return
    # admin = Admin(endpoint="admin",index_view=Dashboard(),base_template='lte-master.html',static_url_path="/static/")
    flaskadmin.template_mode = "bootstrap4"
    flaskadmin.init_app(flask_bp)
    adminlte = AdminLTE3()
    adminlte.init_app(app)

    Events.admin_prehook.notify(flaskadmin=flaskadmin, admin_bp=admin_bp)

    @app.route('/<proxy_path>/admin')
    @app.doc(hide=True)
    def auto_route(proxy_path=None, user_secret=None):
        return redirect(request.url.replace("http://", "https://") + "/")

    flaskadmin.add_view(UserAdmin(User, db.session))
    flaskadmin.add_view(DomainAdmin(Domain, db.session))
    flaskadmin.add_view(AdminstratorAdmin(AdminUser, db.session))
    from .NodeAdmin import NodeAdmin
    flaskadmin.add_view(NodeAdmin(Child, db.session))
    from .Dashboard import Dashboard
    from .SettingAdmin import SettingAdmin
    from .commercial_info import CommercialInfo
    from .ProxyAdmin import ProxyAdmin
    from .Actions import Actions
    from .Backup import Backup
    from .QuickSetup import QuickSetup
    Dashboard.register(admin_bp, route_base="/")
    SettingAdmin.register(admin_bp)
    ProxyAdmin.register(admin_bp)
    Actions.register(admin_bp)
    CommercialInfo.register(admin_bp)
    QuickSetup.register(admin_bp)
    Backup.register(admin_bp)

    # admin_bp.add_url_rule('/admin/quicksetup/',endpoint="quicksetup",view_func=QuickSetup.index,methods=["GET"])
    # admin_bp.add_url_rule('/admin/quicksetup/',endpoint="quicksetup-save", view_func=QuickSetup.save,methods=["POST"])

    app.add_url_rule("/<proxy_path>/admin/static/<filename>/", endpoint="admin.static")  # fix bug in admin with blueprint

    flask_bp.debug = True
    app.register_blueprint(admin_bp, url_prefix=f"/<proxy_path>/admin/",)
    app.register_blueprint(admin_bp, name=f'child_{admin_bp.name}', url_prefix=f"/<proxy_path>/<int:child_id>/admin/")
    app.register_blueprint(flask_bp, url_prefix=f"/<proxy_path>/")
    app.register_blueprint(flask_bp, name=f'child_{flask_bp.name}', url_prefix=f"/<proxy_path>/<int:child_id>/")
