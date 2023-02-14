from flask_admin.contrib import sqla
from hiddifypanel.panel.database import db
from wtforms.validators import Regexp
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,get_hconfigs
from wtforms.validators import Regexp,ValidationError
from .adminlte import AdminLTEModelView
from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _
from hiddifypanel.panel import hiddify
from flask import Markup

class DomainAdmin(AdminLTEModelView):
    list_template = 'model/domain_list.html'    
    edit_modal=True
    
    column_descriptions = dict(
        domain=_("domain.description"),
        mode=_("Direct mode means you want to use your server directly (for usual use), CDN means that you use your server on behind of a CDN provider."),
        cdn_ip=_("config.cdn_forced_host.description"),
        # current_usage_GB="in GB"
    )
    create_modal=True
    can_export = False
    form_args = {
    'domain': {
        'validators': [Regexp(r'^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})$',message=__("Should be a valid domain"))]
    },
    "cdn_ip":{
        'validators':[Regexp(r"(^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d).){3}(25[0-5]|(2[0-4]|1\d|[1-9]|)\d)$)|^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})$",message=__("Invalid IP or domain"))]
    }
    }
    column_list = ["domain","mode","domain_ip","cdn_ip"]
    # column_editable_list=["domain"]
    # column_filters=["domain","mode"]
    column_searchable_list=["domain","mode"]
    column_labels={
        "domain":_("domain.domain"),
        "mode": _("domain.mode"),
        "cdn_ip":_("config.cdn_forced_host.label"),
        'domain_ip':_('domain.ip'),
        }
    def _domain_admin_link(view, context, model, name):
        return Markup(f'<a href="https://{model.domain}{hiddify.get_admin_path()}" class="badge badge-info" target="_blank">{model.domain}</a>')
    def _domain_ip(view, context, model, name):
        dip=hiddify.get_domain_ip(model.domain)
        myip=hiddify.get_ip(4)
        if myip==dip:
            badge_type='success'
        elif dip:
            badge_type='info'
        else:
            badge_type='danger'
        return Markup(f'<span class="badge badge-{badge_type}">{dip}</span>')
    column_formatters = {
        'domain_ip': _domain_ip        ,
        'domain': _domain_admin_link        
    }
    def search_placeholder(self):
            return f"{_('search')} {_('domain.domain')} {_('domain.mode')}"
    # column_list = ["username"]
    # can_edit = False
    # def on_model_change(self, form, model, is_created):
    #     model.password = generate_password_hash(model.password)
    def on_model_change(self, form, model, is_created):
        model.domain = model.domain.lower()
        configs=get_hconfigs()
        for c in configs:
            if "domain" in c and ConfigEnum.decoy_domain!=c:
                if model.domain==configs[c]:
                    raise ValidationError(f"another {model.mode} is exist")    
    
        dip=hiddify.get_domain_ip(model.domain)
        if dip==None:
            raise ValidationError(_("Domain can not be resolved! there is a problem in your domain"))
        
        myip=hiddify.get_ip(4)
        if model.mode==DomainType.direct and myip!=dip:
            raise ValidationError(_("Domain IP=%(domain_ip)s is not matched with your ip=%(server_ip)s which is required in direct mode",server_ip=myip,domain_ip=dip))

        if dip==myip and model.mode in [DomainType.cdn,DomainType.relay]:
            raise ValidationError(_("In CDN mode, Domain IP=%(domain_ip)s should be different to your ip=%(server_ip)s",server_ip=myip,domain_ip=dip))
        
        # if model.mode in [DomainType.ss_faketls, DomainType.telegram_faketls]:
        #     if len(Domain.query.filter(Domain.mode==model.mode and Domain.id!=model.id).all())>0:
        #         ValidationError(f"another {model.mode} is exist")
        model.domain=model.domain.lower()

        if model.mode==DomainType.direct and model.cdn_ip:
            raise ValidationError(f"Specifying CDN IP is only valid for CDN mode")

        hiddify.flash_config_success()

        

    def on_model_delete(self, model):
        if len(Domain.query.all())<=1:
            raise ValidationError(f"at least one domain should exist")    

