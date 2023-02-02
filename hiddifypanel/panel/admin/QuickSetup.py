from hiddifypanel.models import BoolConfig,StrConfig,ConfigEnum,hconfig
from flask_babelex import lazy_gettext as _
# from flask_babelex import gettext as _
import wtforms as wtf
from flask_wtf import FlaskForm, CSRFProtect
from flask_bootstrap import SwitchField
from hiddifypanel.panel import hiddify
from flask_admin.base import expose
# from gettext import gettext as _


import re
from flask import render_template,current_app,flash, Markup,redirect,url_for
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,get_hconfigs
from hiddifypanel.panel.database import db
from wtforms.fields import *


from flask_classful import FlaskView

class QuickSetup(FlaskView):
    
        def index(self):
                return render_template('quick_setup.html', lang_form=get_lang_form(), form=get_quick_setup_form(),ipv4=hiddify.get_ip(4),ipv6=hiddify.get_ip(6))
        def post(self):
                quick_form=get_quick_setup_form()
                lang_form=get_lang_form()
                if lang_form.lang_submit.data:
                        if lang_form.validate_on_submit():
                                StrConfig.query.filter(StrConfig.key==ConfigEnum.lang).first().value=lang_form.lang.data
                                db.session.commit()
                                flash(_('quicksetup.setlang.success'), 'success')
                                from flask_babel import refresh; refresh()
                        else:
                                flash(_('quicksetup.setlang.error'), 'danger')

                        return render_template('quick_setup.html', form=get_quick_setup_form(True),lang_form=lang_form)                

                if quick_form.validate_on_submit():
                        sslip_dm=Domain.query.filter(Domain.domain==f'{hiddify.get_ip(4)}.sslip.io').first()
                        db.session.remove(sslip_dm)

                        data=[Domain(domain=quick_form.domain.data,mode=DomainType.direct),]
                        
                        db.session.bulk_save_objects(data)
                        
                        BoolConfig.query.filter(BoolConfig.key==ConfigEnum.telegram_enable).first().value=quick_form.enable_telegram.data
                        BoolConfig.query.filter(BoolConfig.key==ConfigEnum.vmess_enable).first().value=quick_form.enable_vmess.data
                        db.session.commit()
                        hiddify.flash_config_success()
                else:
                        flash(_('config.validation-error'), 'danger')
                return render_template('quick_setup.html', form=quick_form,lang_form=get_lang_form(True))

def get_lang_form(empty=False):
        class LangForm(FlaskForm):
                lang=wtf.fields.SelectField(_("config.lang.label"),choices=[("en",_("lang.en")),("fa",_("lang.fa"))],description=_("config.lang.description"),default=hconfig(ConfigEnum.lang))
                lang_submit=wtf.fields.SubmitField(_('Submit'))
        
        return LangForm(None)if empty else LangForm()
def get_quick_setup_form(empty=False):
        def get_used_domains():
                configs=get_hconfigs()
                domains=[]
                for c in configs:
                        if "domain" in c:
                                domains.append(configs[c])
                for d in Domain.query.all():
                        domains.append(d.domain)
                return domains
        class QuickSetupForm(FlaskForm):
                domain_validators=[wtf.validators.Regexp("^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})$",re.IGNORECASE,_("config.Invalid domain")),
                                        wtf.validators.NoneOf(get_used_domains(),_("config.Domain already used"))]
                domain=wtf.fields.StringField(_("domain.domain"),domain_validators,description=_("domain.description"),render_kw={"pattern":domain_validators[0].regex.pattern,"title":domain_validators[0].message,"required":""})
                enable_telegram=SwitchField(_("config.telegram_enable.label"),description=_("config.telegram_enable.description"),default=hconfig(ConfigEnum.telegram_enable))
                enable_vmess=SwitchField(_("config.vmess_enable.label"),description=_("config.vmess_enable.description"),default=hconfig(ConfigEnum.vmess_enable))
                submit=wtf.fields.SubmitField(_('Submit'))
        
        return QuickSetup(None) if empty else QuickSetupForm()