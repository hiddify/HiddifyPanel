from flask_admin.contrib import sqla
from hiddifypanel.panel.database import db
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,hconfig
from flask import Markup,g
from wtforms.validators import Regexp,ValidationError
import re,uuid
from hiddifypanel import xray_api
from .adminlte import AdminLTEModelView
# from gettext import gettext as _
from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _
from hiddifypanel.panel import hiddify
from hiddifypanel.panel.hiddify import flash

class UserAdmin(AdminLTEModelView):
    
    list_template = 'model/user_list.html'    
    form_excluded_columns=['last_reset_time']
    edit_modal=True
    create_modal=True
    # column_display_pk = True
    # can_export = True

    
    form_args = {
    'uuid': {
        'validators': [Regexp(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',message=__("Should be a valid uuid"))]
    #     'label': 'First Name',
    #     'validators': [required()]
    }
    }
    # column_labels={'uuid':_("user.UUID")}
    # column_filters=["uuid","name","usage_limit_GB",'monthly',"current_usage_GB","expiry_time"]
    
    column_labels={
        "Actions":_("actions"),
        "name": _("user.name"),
        "UserLinks":_("user.user_links"),
        "usage_limit_GB":_("user.usage_limit_GB"),
        "monthly":_("Reset every month"),
        "current_usage_GB":_("user.current_usage_GB"),
        "expiry_time":_("user.expiry_time"),
        # "last_reset_time":_("user.last_reset_time"),
        "uuid":_("user.UUID"),
     }
    column_searchable_list=[("uuid"),"name"]
    def search_placeholder(self):
        return f"{_('search')} {_('user.UUID')} {_('user.name')}"
    # def get_column_name(self,field):
    #         return "x"
    #  return column_labels[field]
    column_descriptions = dict(
        # name=_'just for remembering',
        # usage_limit_GB="in GB",
        # current_usage_GB="in GB"
    )
    column_editable_list=["name","usage_limit_GB","current_usage_GB","expiry_time"]
    # form_extra_fields={
    #     'uuid': {'label_name':"D"}
        
    #     }
    column_list = ["name","UserLinks","current_usage_GB","usage_limit_GB",'monthly',"expiry_time","uuid",]
    # can_edit = False
    # def on_model_change(self, form, model, is_created):
    #     model.password = generate_password_hash(model.password)
    
    
    def _ul_formatter(view, context, model, name):
        
        return Markup(" ".join([hiddify.get_user_link(model.uuid,d) for d in Domain.query.all()]))
    def _uuid_formatter(view, context, model, name):
        return Markup(f"<span>{model.uuid}</span>")
    def _usage_formatter(view, context, model, name):
        return round(model.current_usage_GB,3)
    column_formatters = {
        'UserLinks': _ul_formatter,
        'uuid': _uuid_formatter,
        'current_usage_GB': _usage_formatter
    }
    def on_model_delete(self, model):
        if len(User.query.all())<=1:
            raise ValidationError(f"at least one user should exist")    
        xray_api.remove_client(model.uuid)
        hiddify.flash_config_success()

        
    # def is_accessible(self):
    #     return g.is_admin

    def on_model_change(self, form, model, is_created):
        if len(User.query.all())%4==0:
            flash(('<div id="show-modal-donation"></div>'), ' d-none')
        if not re.match("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", model.uuid):
            raise ValidationError('Invalid UUID e.g.,'+ str(uuid.uuid4()))
        else:
            super().on_model_change(form, model, is_created)
        
        
        # if model.current_usage_GB < model.usage_limit_GB:
        #     xray_api.add_client(model.uuid)
        # else:
        #     xray_api.remove_client(model.uuid)
        hiddify.flash_config_success()
        
