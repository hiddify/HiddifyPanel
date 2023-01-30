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
class UserAdmin(AdminLTEModelView):
    column_display_pk = True
    can_export = True

    
    # form_args = {
    # 'name': {
    #     'label': 'First Name',
    #     'validators': [required()]
    # }
    # }
    # column_labels={'uuid':_("user.UUID")}
    column_filters=["uuid","name","monthly_usage_limit_GB","current_usage_GB","expiry_time"]
    
    column_labels={
        "uuid":_("user.UUID"),
        "name": _("user.name"),
        "monthly_usage_limit_GB":_("user.monthly_usage_limit_GB"),
        "current_usage_GB":_("user.current_usage_GB"),
        "expiry_time":_("user.expiry_time"),
        "last_reset_time":_("user.last_reset_time"),
        "UserLinks":_("user.user_links"),
        "Actions":_("actions")
     }
    column_searchable_list=[("uuid"),"name"]
    def search_placeholder(self):
        return f"{_('search')} {_('user.UUID')} {_('user.name')}"
    # def get_column_name(self,field):
    #         return "x"
    #  return column_labels[field]
    column_descriptions = dict(
        # name=_'just for remembering',
        # monthly_usage_limit_GB="in GB",
        # current_usage_GB="in GB"
    )
    column_editable_list=["name","monthly_usage_limit_GB","current_usage_GB","expiry_time"]
    # form_extra_fields={
    #     'uuid': {'label_name':"D"}
        
    #     }
    column_list = ["uuid","name","monthly_usage_limit_GB","current_usage_GB","expiry_time","UserLinks"]
    # can_edit = False
    # def on_model_change(self, form, model, is_created):
    #     model.password = generate_password_hash(model.password)
    
    def _ul_formatter(view, context, model, name):
        proxy_path=hconfig(ConfigEnum.proxy_path)
        return Markup(" ".join([f"""<a target='_blank' href='https://{d.domain}/{proxy_path}/{model.uuid}/'><span class='badge badge-info ltr'>{f'<span class="badge badge-success" >{_("domain.cdn")}</span> ' if d.mode!=DomainType.cdn else ''}{d.domain}</span></a>""" 
            for d in Domain.query.filter(Domain.mode == DomainType.cdn or Domain.mode == DomainType.direct).all()]))
    def _uuid_formatter(view, context, model, name):
        return Markup(f"<span>{model.uuid}</span>")
    column_formatters = {
        'UserLinks': _ul_formatter,
        'uuid': _uuid_formatter,
    }
    def on_model_delete(self, model):
        xray_api.remove_client(model.uuid)
        
    # def is_accessible(self):
    #     return g.is_admin

    def on_model_change(self, form, model, is_created):
        
        if not re.match("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", model.uuid):
            raise ValidationError('Invalid UUID e.g.,'+ str(uuid.uuid4()))
        else:
            super().on_model_change(form, model, is_created)
        
        
        # if model.current_usage_GB < model.monthly_usage_limit_GB:
        #     xray_api.add_client(model.uuid)
        # else:
        #     xray_api.remove_client(model.uuid)
        
