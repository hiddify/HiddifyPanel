from flask_admin.contrib import sqla
from hiddifypanel.panel.database import db
from wtforms.validators import Regexp
from hiddifypanel.models import *
from wtforms.validators import Regexp, ValidationError
from .adminlte import AdminLTEModelView
from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _
from hiddifypanel.panel import hiddify,hiddify_api,cf_api
from flask import Markup
from flask import Flask,g,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms import SelectMultipleField
import datetime

from wtforms.widgets import ListWidget, CheckboxInput
from sqlalchemy.orm import backref
# Define a custom field type for the related domains
from flask_admin.form.fields import Select2TagsField,Select2Field



class AdminstratorAdmin(AdminLTEModelView):
    column_hide_backrefs = False
    column_list = ["name",'UserLinks','mode','comment','users']
    form_columns = ["name",'mode','comment',"uuid"]
    list_template = 'model/admin_list.html'
    # edit_modal = True
    # form_overrides = {'work_with': Select2Field}
    form_widget_args = {
    'description': {
        'rows': 100,
        'style': 'font-family: monospace; direction:ltr'
    }
    }
    column_labels = {
        "Actions":_("actions"),
        "UserLinks":_("user.user_links"),
        "name": _("user.name"),
        "mode":_("Mode"),
        "uuid":_("user.UUID"),
        "comment":_("Note"),

    }
    
    column_descriptions = dict(
        comment=_("Add some text that is only visible to super_admin."),
        mode=_("Define the admin mode. "),
    )
    # create_modal = True
    can_export = False
    
    # column_list = ["domain",'sub_link_only', "mode","alias", "domain_ip", "cdn_ip"]
    # column_editable_list=["domain"]
    # column_filters=["domain","mode"]
    form_excluded_columns=['telegram_id']
    column_exclude_list=['telegram_id']
    
    column_searchable_list = ["name", "uuid"]
    
    # form_columns=['domain','sub_link_only','alias','mode','cdn_ip','show_domains']

    def _ul_formatter(view, context, model, name):
        
        return Markup(" ".join([hiddify.get_user_link(model.uuid,d,'admin',model.name) for d in get_panel_domains()]))
    
    def _name_formatter(view, context, model, name):
        proxy_path=hconfig(ConfigEnum.proxy_path)
        d=get_panel_domains()[0]
        if d:
            link=f"<a target='_blank' href='https://{d.domain}/{proxy_path}/{model.uuid}/admin/#{model.name}'>{model.name} <i class='fa-solid fa-arrow-up-right-from-square'></i></a>"
            return Markup(link)
        else:
            return model.name

    def _users_formatter(view, context, model, name):
        last_day=datetime.datetime.now()-datetime.timedelta(days=1)
        onlines=[p for p in  model.users  if p.last_online and p.last_online>last_day]
        return Markup(f"<a class='btn btn-xs' href='{url_for('flask.user.index_view',admin_id=model.id)}'>{len(model.users)} {_('Users')}<br> {len(onlines)} {_('Online Users')}</a>")
        
        
        # return Markup(f"<span class='badge ltr badge-{'success' if days>7 else ('warning' if days>0 else 'danger') }'>{days}</span> "+_('days'))

    column_formatters = {
        'name': _name_formatter,
        'users': _users_formatter,
        'UserLinks':_ul_formatter
        
    }
    def search_placeholder(self):
        return f"{_('search')} {_('user.UUID')} {_('user.name')}"


    def is_accessible(self):
        return g.admin.mode==AdminMode.super_admin