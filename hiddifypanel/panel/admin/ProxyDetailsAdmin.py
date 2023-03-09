from flask_admin.contrib import sqla
from hiddifypanel.panel.database import db
from wtforms.validators import Regexp
from hiddifypanel.models import User, Domain, DomainType, StrConfig, ConfigEnum, get_hconfigs,ShowDomain
from wtforms.validators import Regexp, ValidationError
from .adminlte import AdminLTEModelView
from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _
from hiddifypanel.panel import hiddify
from flask import Markup
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms import SelectMultipleField


from wtforms.widgets import ListWidget, CheckboxInput
from sqlalchemy.orm import backref
# Define a custom field type for the related domains
from flask_admin.form.fields import Select2TagsField,Select2Field



class ProxyDetailsAdmin(AdminLTEModelView):
    column_hide_backrefs = True
    form_excluded_columns=['child']
    column_exclude_list =['child']
    list_template = 'model/domain_list.html'
    # edit_modal = True
    # form_overrides = {'work_with': Select2Field}

    