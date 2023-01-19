from flask_admin.contrib import sqla
from hiddifypanel.panel.database import db
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,hconfig
from flask import Markup
from wtforms.validators import Regexp,ValidationError
import re,uuid
class UserAdmin(sqla.ModelView):
    column_display_pk = True
    can_export = True

    column_searchable_list=["uuid",'name']
    # form_args = {
    # 'name': {
    #     'label': 'First Name',
    #     'validators': [required()]
    # }
    # }
    column_descriptions = dict(
        name='just for remembering',
        monthly_usage_limit_GB="in GB",
        current_usage_GB="in GB"
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
        return Markup(" ".join([f"<a href='https://{d.domain}/{proxy_path}/{model.uuid}/'>{'CDN: ' if d.mode==DomainType.cdn else ''}{d.domain}</a>" 
            for d in Domain.query.filter(Domain.mode == DomainType.cdn or Domain.mode == DomainType.direct).all()]))

    column_formatters = {
        'UserLinks': _ul_formatter,
    }
    def on_model_change(self, form, model, is_created):
        
        if not re.match("^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$", model.uuid):
            raise ValidationError('Invalid UUID e.g.,'+ str(uuid.uuid4()))
        else:
            super().on_model_change(form, model, is_created)