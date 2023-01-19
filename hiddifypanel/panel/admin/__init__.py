from flask import Blueprint,url_for
from flask_admin import Admin
from .UserAdmin import UserAdmin
from .DomainAdmin import DomainAdmin
from .ConfigAdmin import ConfigAdmin
from hiddifypanel.models import  StrConfig,ConfigEnum
# from .resources import ProductItemResource, ProductResource
from hiddifypanel.panel.database import db
from hiddifypanel.models import User,Domain,BoolConfig,StrConfig
from .dashboard import Dashboard
from .actions import Actions
from flask_admin.menu import MenuLink
from . import actions 


bp = Blueprint("admin2", __name__, url_prefix=f"/admin/",template_folder="templates")
admin = Admin(index_view=Dashboard())
def init_app(app):
    # admin_secret=StrConfig.query.filter(StrConfig.key==ConfigEnum.admin_secret).first()
    # 

    admin.template_mode = app.config.FLASK_ADMIN_TEMPLATE_MODE
    # bp.add_url_rule("/actions/reverselog/<logfile>", view_func=actions.reverselog)
    # bp.add_url_rule("/actions/apply_configs", view_func=actions.apply_configs)
    # bp.add_url_rule("/actions/change", view_func=actions.change)
    # bp.add_url_rule("/actions/reinstall", view_func=actions.reinstall)
    # bp.add_url_rule("/actions/status", view_func=actions.status)
    # bp.add_url_rule("/actions/update", view_func=actions.update)
    # bp.add_url_rule("/actions/config", view_func=actions.config)

    
    admin.init_app(app)
    app.register_blueprint(bp)
    admin.add_view(UserAdmin(User, db.session))
    
    admin.add_view(DomainAdmin(Domain, db.session))
    admin.add_view(ConfigAdmin(BoolConfig, db.session))
    admin.add_view(ConfigAdmin(StrConfig, db.session))
    admin.add_view(Actions(name="actions",endpoint='customviews'))
    admin.add_link(MenuLink(name='Apply Changes', category='', url="actions/apply_configs"))
    # admin.
    
    

