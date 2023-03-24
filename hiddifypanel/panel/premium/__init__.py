from .parent_domain import ParentDomain
from .ParentDomainAdmin import ParentDomainAdmin
from hiddifypanel.panel.admin import flask_bp
from hiddifypanel.panel.admin import admin_bp
    
    
def init_app(app):
    admin.add_view(ParentDomainAdmin(ParentDomain, db.session))
    