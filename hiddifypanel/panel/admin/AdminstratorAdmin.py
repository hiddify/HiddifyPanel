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
from wtforms import SelectField

class AdminModeField(SelectField):
    def __init__(self, label=None, validators=None, **kwargs):
        super(AdminModeField, self).__init__(label, validators, **kwargs)
        if g.admin.mode==AdminMode.slave:
            self.choices = [ (AdminMode.slave.value, 'Slave')]
        elif g.admin.mode==AdminMode.admin:
            self.choices = [ (AdminMode.slave.value, 'Slave'),(AdminMode.admin.value, 'Admin'),]
        elif g.admin.mode==AdminMode.super_admin:
            self.choices = [(AdminMode.slave.value, 'Slave'),(AdminMode.admin.value, 'Admin'),(AdminMode.super_admin.value, 'Super Admin')]



class SubAdminsField(SelectField):
    def __init__(self, label=None, validators=None,*args, **kwargs):
        kwargs.pop("allow_blank")
        super().__init__(label, validators,*args, **kwargs)
        self.choices=[(admin.id,admin.name) for admin in g.admin.sub_admins]
        self.choices+=[(g.admin.id,g.admin.name)]
class AdminstratorAdmin(AdminLTEModelView):
    column_hide_backrefs = False
    column_list = ["name",'UserLinks','mode','comment','users']
    form_columns = ["name",'mode','comment',"uuid"]
    list_template = 'model/admin_list.html'
    # edit_modal = True
    # form_overrides = {'work_with': Select2Field}
    
    form_overrides = {
        'mode': AdminModeField,
        'parent_admin': SubAdminsField
    }
    column_labels = {
        "Actions":_("actions"),
        "UserLinks":_("user.user_links"),
        "name": _("user.name"),
        "mode":_("Mode"),
        "uuid":_("user.UUID"),
        "comment":_("Note"),
        "users":_("Users"),

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
            if model.parent_admin:
                return Markup(model.parent_admin.name +"&rlm; / &rlm;"+link)
            return Markup(link)
        else:
            return model.name

    def _users_formatter(view, context, model, name):
        last_day=datetime.datetime.now()-datetime.timedelta(days=1)
        onlines=[p for p in  model.users  if p.last_online and p.last_online>last_day]
        return Markup(f"<a class='btn btn-xs' href='{url_for('flask.user.index_view',admin_id=model.id)}'>{_('Users')}: {len(model.users)} <br> {_('Online Users')}: {len(onlines)} </a>")
        
        
        # return Markup(f"<span class='badge ltr badge-{'success' if days>7 else ('warning' if days>0 else 'danger') }'>{days}</span> "+_('days'))

    column_formatters = {
        'name': _name_formatter,
        'users': _users_formatter,
        'UserLinks':_ul_formatter
        
    }
    def search_placeholder(self):
        return f"{_('search')} {_('user.UUID')} {_('user.name')}"


    # def is_accessible(self):
    #     return g.admin.mode==AdminMode.super_admin


    def get_query(self):
            # Get the base query
        query = super().get_query()

        admin_ids=g.admin.recursive_sub_admins_ids()
        query = query.filter(AdminUser.id.in_(admin_ids))

        return query

    # Override get_count_query() to include the filter condition in the count query
    def get_count_query(self):
        # Get the base count query
        query = super().get_count_query()

        admin_ids=g.admin.recursive_sub_admins_ids()
        query = query.filter(AdminUser.id.in_(admin_ids))

        return query


    def on_model_change(self, form, model, is_created):
        # if model.id==1:
        #     model.parent_admin_id=0
        #     model.parent_admin=None
        # else:
        #     model.parent_admin_id=1
        #     model.parent_admin=AdminUser.query.filter(AdminUser.id==1).first()
        if model.id!=1 and model.parent_admin==None:
            model.parent_admin_id=g.admin.id
            model.parent_admin=g.admin

        if g.admin.mode!=AdminMode.super_admin and model.mode==AdminMode.super_admin:
            raise ValidationError("Sub-Admin can not have more power!!!!")
        if model.mode==AdminMode.slave and model.mode!=AdminMode.slave:
            raise ValidationError("Sub-Admin can not have more power!!!!")
    def on_model_delete(self, model):
        if model.id==1:
            raise ValidationError(_("Owner can not be deleted!"))



    def get_query_for_parent_admin(self):
        admin_user_id = self.get_pk_value()
        sub_admins_ids = set(recursive_sub_admins_ids(AdminUser.query.get(admin_user_id)))
        return AdminUser.query.filter(AdminUser.id.in_(sub_admins_ids)).with_entities(AdminUser.id, AdminUser.name)


    def on_form_prefill(self, form, id=None):
        if form._obj is not None and form._obj.id==1:
            del form.parent_admin
        
        # if g.admin.mode==AdminMode.slave:
        del form.mode
        
