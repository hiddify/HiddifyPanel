from flask_admin.contrib import sqla
from hiddifypanel.panel.database import db
from wtforms.validators import Regexp
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum
from wtforms.validators import Regexp,ValidationError
class DomainAdmin(sqla.ModelView):
    can_export = True
    form_args = {
    'domain': {
        'validators': [Regexp(r'^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})$',message="Should be a valid domain")]
    }
    }
    column_editable_list=["domain","mode"]
    column_searchable_list=["domain"]
    # column_list = ["username"]
    # can_edit = False
    # def on_model_change(self, form, model, is_created):
    #     model.password = generate_password_hash(model.password)
    def on_model_change(self, form, model, is_created):
        model.domain = model.domain.lower()
        if model.mode in [DomainType.ss_faketls, DomainType.telegram_faketls]:
            if len(Domain.query.filter(Domain.mode==model.mode and Domain.id!=model.id).all())>0:
                ValidationError(f"another {model.mode} is exist")

    pass