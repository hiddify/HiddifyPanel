from hiddifypanel.models import BoolConfig,StrConfig,ConfigEnum,hconfig
from flask_babelex import lazy_gettext as _
# from flask_babelex import gettext as _
import wtforms as wtf
from flask_wtf import FlaskForm, CSRFProtect
from flask_bootstrap import SwitchField

from flask_admin.base import expose
# from gettext import gettext as _


import re
from flask import render_template,current_app,flash, Markup
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,get_hconfigs
from hiddifypanel.panel.database import db
from wtforms.fields import *



    
def index():
        return render_template('quick_setup.html', form=QuickSetupForm())
def save():
        form=QuickSetupForm()
        if form.validate_on_submit():
            flash(_('config.validation-success'), 'success')
            return render_template('config.html', form=form)
        flash(_('config.validation-error'), 'danger')
        return render_template('quick_setup.html', form=form)

class QuickSetupForm(FlaskForm):
    domain_validators=[wtf.validators.Regexp("^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})$",re.IGNORECASE,_("config.Invalid domain"))]
    domain=wtf.fields.StringField(_("domain.domain"),domain_validators,description=_("domain.description"))
    enable_telegram=SwitchField(_("config.telegram_enable.label"),description=_("config.telegram_enable.description"))
    enable_vmess=SwitchField(_("config.vmess_enable.label"),description=_("config.vmess_enable.description"))
    submit=wtf.fields.SubmitField(_('Submit'))