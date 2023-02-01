from flask_admin.contrib import sqla
from hiddifypanel.panel.database import db
from wtforms.validators import Regexp
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,get_hconfigs
from wtforms.validators import Regexp,ValidationError
from .adminlte import AdminLTEModelView
from flask_babelex import lazy_gettext as _
class ProxyAdmin(AdminLTEModelView):
    can_export = True
    can_delete = False
    can_create  = False
    column_editable_list=["enable"]
    column_filters=["name","transport","l3","cdn","proto"]
    column_searchable_list=["name","transport","l3","cdn","proto"]
    column_labels={
        "name":_("proxy.name"),
        "proto": _("proxy.protocol"),
        "transport": _("proxy.transport"),
        "l3": _("proxy.l3"),
        "cdn": _("proxy.cdn"),
        }
    form_widget_args = {
        'name': {'readonly': True},
        'proto': {'readonly': True},
        'transport': {'readonly': True},
        'l3': {'readonly': True},
        'cdn': {'readonly': True},
    }
    def search_placeholder(self):
            return f"{_('search')}"
    # column_list = ["username"]
    # can_edit = False
    # def on_model_change(self, form, model, is_created):
    #     model.password = generate_password_hash(model.password)
    def on_model_change(self, form, model, is_created):
        pass