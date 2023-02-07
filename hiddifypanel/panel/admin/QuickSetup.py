from hiddifypanel.models import BoolConfig,StrConfig,ConfigEnum,hconfig
# from flask_babelex import lazy_gettext as _
from flask_babelex import gettext as _
import wtforms as wtf
from flask_wtf import FlaskForm
from flask_bootstrap import SwitchField
from hiddifypanel.panel import hiddify
from flask_admin.base import expose
# from gettext import gettext as _
from wtforms.validators import Regexp,ValidationError

import re
from flask import render_template,current_app, Markup,redirect,url_for
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,get_hconfigs
from hiddifypanel.panel.database import db
from wtforms.fields import *

from hiddifypanel.panel.hiddify import flash
from flask_classful import FlaskView

class QuickSetup(FlaskView):
    
        def index(self):
                return render_template('quick_setup.html', lang_form=get_lang_form(), form=get_quick_setup_form(),ipv4=hiddify.get_ip(4),ipv6=hiddify.get_ip(6),admin_link=admin_link())
        
        def post(self):
                quick_form=get_quick_setup_form()
                lang_form=get_lang_form()
                if lang_form.lang_submit.data:
                        if lang_form.validate_on_submit():
                                StrConfig.query.filter(StrConfig.key==ConfigEnum.lang).first().value=lang_form.lang.data
                                StrConfig.query.filter(StrConfig.key==ConfigEnum.admin_lang).first().value=lang_form.admin_lang.data
                                db.session.commit()
                                flash((_('quicksetup.setlang.success')), 'success')
                                from flask_babel import refresh; refresh()
                        else:
                                flash((_('quicksetup.setlang.error')), 'danger')

                        return render_template('quick_setup.html', form=get_quick_setup_form(True),lang_form=lang_form,admin_link=admin_link())                
                
                if quick_form.validate_on_submit():
                        sslip_dm=Domain.query.filter(Domain.domain==f'{hiddify.get_ip(4)}.sslip.io').delete()

                        data=[Domain(domain=quick_form.domain.data.lower(),mode=DomainType.direct),]
                        
                        db.session.bulk_save_objects(data)
                        
                        BoolConfig.query.filter(BoolConfig.key==ConfigEnum.telegram_enable).first().value=quick_form.enable_telegram.data
                        BoolConfig.query.filter(BoolConfig.key==ConfigEnum.vmess_enable).first().value=quick_form.enable_vmess.data
                        BoolConfig.query.filter(BoolConfig.key==ConfigEnum.firewall).first().value=quick_form.enable_firewall.data
                        BoolConfig.query.filter(BoolConfig.key==ConfigEnum.block_iran_sites).first().value=quick_form.block_iran_sites.data
                        StrConfig.query.filter(StrConfig.key==ConfigEnum.decoy_domain).first().value=quick_form.decoy_domain.data
                        db.session.commit()
                        hiddify.flash_config_success()
                        proxy_path=hconfig(ConfigEnum.proxy_path)
                        uuid=User.query.first().uuid
                        userlink=f"<a class='btn btn-secondary share-link' target='_blank' href='https://{quick_form.domain.data}/{proxy_path}/{uuid}/'>{_('default user link')}</a>"
                        flash((_('The default user link is %(link)s. To add or edit more users, please visit users from menu.',link=userlink)),'info')
                else:
                        flash(_('config.validation-error'), 'danger')
                return render_template('quick_setup.html', form=quick_form,lang_form=get_lang_form(True),ipv4=hiddify.get_ip(4),ipv6=hiddify.get_ip(6),admin_link=admin_link() )

def get_lang_form(empty=False):
        class LangForm(FlaskForm):
                admin_lang=wtf.fields.SelectField(_("config.admin_lang.label"),choices=[("en",_("lang.en")),("fa",_("lang.fa"))],description=_("config.admin_lang.description"),default=hconfig(ConfigEnum.admin_lang))
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
                domain_regex="^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})$"

                domain_validators=[wtf.validators.Regexp(domain_regex,re.IGNORECASE,_("config.Invalid domain")),
                                        validate_domain,
                                        wtf.validators.NoneOf([d.domain.lower() for d in Domain.query.all()],_("config.Domain already used")),
                                        wtf.validators.NoneOf([c.value.lower() for c in StrConfig.query.all() if "fakedomain" in c.key and c.key!=ConfigEnum.decoy_domain],_("config.Domain already used"))
                                        ]
                domain=wtf.fields.StringField(_("domain.domain"),domain_validators,description=_("domain.description"),render_kw={"pattern":domain_validators[0].regex.pattern,"title":domain_validators[0].message,"required":"","placeholder":"sub.domain.com"})
                enable_telegram=SwitchField(_("config.telegram_enable.label"),description=_("config.telegram_enable.description"),default=hconfig(ConfigEnum.telegram_enable))
                enable_vmess=SwitchField(_("config.vmess_enable.label"),description=_("config.vmess_enable.description"),default=hconfig(ConfigEnum.vmess_enable))
                enable_firewall=SwitchField(_("config.firewall.label"),description=_("config.firewall.description"),default=hconfig(ConfigEnum.firewall))
                block_iran_sites=SwitchField(_("config.block_iran_sites.label"),description=_("config.block_iran_sites.description"),default=hconfig(ConfigEnum.block_iran_sites))
                decoy_domain=wtf.fields.StringField(_("config.decoy_domain.label"),description=_("config.decoy_domain.description"),default=hconfig(ConfigEnum.decoy_domain),validators=[wtf.validators.Regexp(domain_regex,re.IGNORECASE,_("config.Invalid domain"))])
                submit=wtf.fields.SubmitField(_('Submit'))

                
        
        return QuickSetupForm(None) if empty else QuickSetupForm()
def validate_domain(form,field):
        domain=field.data
        dip=hiddify.get_domain_ip(domain)
        if dip==None:
                raise ValidationError(_("Domain can not be resolved! there is a problem in your domain"))

        myip=hiddify.get_ip(4)
        if dip and myip!=dip:
                raise ValidationError(_("Domain (%(domain)s)-> IP=%(domain_ip)s is not matched with your ip=%(server_ip)s which is required in direct mode",server_ip=myip,domain_ip=dip,domain=domain))
def admin_link():
        return "https://"+Domain.query.first().domain+hiddify.get_admin_path()