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
from flask import Flask,g
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms import SelectMultipleField


from wtforms.widgets import ListWidget, CheckboxInput
from sqlalchemy.orm import backref
# Define a custom field type for the related domains
from flask_admin.form.fields import Select2TagsField,Select2Field



class DomainAdmin(AdminLTEModelView):
    column_hide_backrefs = False
    
    list_template = 'model/domain_list.html'
    # edit_modal = True
    # form_overrides = {'work_with': Select2Field}
    form_widget_args = {
    'description': {
        'rows': 100,
        'style': 'font-family: monospace; direction:ltr'
    }
    }
    column_descriptions = dict(
        domain=_("domain.description"),
        mode=_("Direct mode means you want to use your server directly (for usual use), CDN means that you use your server on behind of a CDN provider."),
        cdn_ip=_("config.cdn_forced_host.description"),
        show_domains=_('You can select the configs with which domains show be shown in the user area. If you select all, automatically, all the new domains will be added for each users.'),
        alias=_('The name shown in the configs for this domain.')
    )
    
    # create_modal = True
    can_export = False
    form_widget_args={'show_domains':{'class':'form-control ltr'}}
    form_args = {
        
        'domain': {
            'validators': [Regexp(r'^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})$', message=__("Should be a valid domain"))]
        },
        "cdn_ip": {
            'validators': [Regexp(r"(((((25[0-5]|(2[0-4]|1\d|[1-9]|)\d).){3}(25[0-5]|(2[0-4]|1\d|[1-9]|)\d))|^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,}))[ \t\n,;]*\w{3}[ \t\n,;]*)*", message=__("Invalid IP or domain"))]
        }
    }
    column_list = ["domain", "mode","alias", "domain_ip", "cdn_ip"]
    # column_editable_list=["domain"]
    # column_filters=["domain","mode"]
    # form_excluded_columns=['work_with']
    column_searchable_list = ["domain", "mode"]
    column_labels = {
        "domain": _("domain.domain"),
        "mode": _("domain.mode"),
        "cdn_ip": _("config.cdn_forced_host.label"),
        'domain_ip': _('domain.ip'),
        'show_domains':_('Show Domains'),
        'alias':_('Alias')
    }

    form_columns=['domain','alias','mode','cdn_ip','show_domains']

    def _domain_admin_link(view, context, model, name):
        if model.mode==DomainType.fake:
            return Markup(f"<span class='badge'>{model.domain}</span>")
        admin_link = f'https://{model.domain}{hiddify.get_admin_path()}'
        return Markup(f'<div class="btn-group"><a href="{admin_link}" class="btn btn-xs btn-secondary">'+_("admin link")+f'</a><a href="{admin_link}" class="btn btn-xs btn-info ltr" target="_blank">{model.domain}</a></div>')

    def _domain_ip(view, context, model, name):
        dip = hiddify.get_domain_ip(model.domain)
        myip = hiddify.get_ip(4)
        if myip == dip and model.mode == DomainType.direct:
            badge_type = ''
        elif dip and model.mode != DomainType.direct and myip != dip:
            badge_type = 'warning'
        else:
            badge_type = 'danger'
        return Markup(f'<span class="badge badge-{badge_type}">{dip}</span>')
    column_formatters = {
        'domain_ip': _domain_ip,
        'domain': _domain_admin_link
    }

    def search_placeholder(self):
        return f"{_('search')} {_('domain.domain')} {_('domain.mode')}"

    # def on_form_prefill(self, form, id):
        # Get the Domain object being edited
        # domain = self.session.query(Domain).get(id)

        # Pre-select the related domains in the checkbox list
        # form.show_domains = [d.id for d in Domain.query.all()]
        

    def on_model_change(self, form, model, is_created):
        model.domain = model.domain.lower()
        configs = get_hconfigs()
        for c in configs:
            if "domain" in c and ConfigEnum.decoy_domain != c:
                if model.domain == configs[c]:
                    raise ValidationError(
                        _("You have used this domain in: ")+_(f"config.{c}.label"))
        myip = hiddify.get_ip(4)
        
        skip_check=False
        if hconfig(ConfigEnum.cloudflare):
            if model.mode==DomainType.direct:
                cf_api.add_or_update_domain(domain, myip,"A",proxied=False)
            elif model.mode==DomainType.cdn or model.mode==DomainType.auto_cdn_ip:
                cf_api.add_or_update_domain(domain, myip,"A",proxied=True)
            skip_check=True
        # elif model.mode==DomainType.auto_cdn_ip:
            
        #     raise ValidationError(_("You have to add your cloudflare api key to use this feature: "))


        dip = hiddify.get_domain_ip(model.domain)
        if not skip_check:
            if dip == None :        
                raise ValidationError(
                    _("Domain can not be resolved! there is a problem in your domain"))

            
            if model.mode == DomainType.direct and myip != dip:
                raise ValidationError(
                    _("Domain IP=%(domain_ip)s is not matched with your ip=%(server_ip)s which is required in direct mode", server_ip=myip, domain_ip=dip))

            if dip == myip and model.mode in [DomainType.cdn, DomainType.relay, DomainType.fake,DomainType.auto_cdn_ip]:
                raise ValidationError(
                    _("In CDN mode, Domain IP=%(domain_ip)s should be different to your ip=%(server_ip)s", server_ip=myip, domain_ip=dip))

            # if model.mode in [DomainType.ss_faketls, DomainType.telegram_faketls]:
            #     if len(Domain.query.filter(Domain.mode==model.mode and Domain.id!=model.id).all())>0:
            #         ValidationError(f"another {model.mode} is exist")
        model.domain = model.domain.lower()
        if model.mode == DomainType.direct and model.cdn_ip:
            raise ValidationError(
                f"Specifying CDN IP is only valid for CDN mode")

            

        if model.mode == DomainType.fake and not model.cdn_ip:
            model.cdn_ip = myip
        
        # if model.mode==DomainType.fake and model.cdn_ip!=myip:
        #     raise ValidationError(f"Specifying CDN IP is only valid for CDN mode")

        # work_with_ids = form.work_with.data
        # print(work_with_ids)
        # # Update the many-to-many relationship
        if len(model.show_domains)==Domain.query.count():
            model.show_domains=[]
        # if model.alias and not g.is_commercial:
            #     model.alias= "@hiddify "+model.alias
        # model.work_with = self.session.query(Domain).filter(
        #     Domain.id.in_(work_with_ids)).all()
        if is_created or not get_domain(model.domain) :
            # return hiddify.reinstall_action(complete_install=False, domain_changed=True)
            hiddify.flash_config_success(restart_mode='apply', domain_changed=True)

    # def after_model_change(self,form, model, is_created):
    #     if model.show_domains.count==0:
    #         db.session.bulk_save_objects(ShowDomain(model.id,model.id))

    def on_model_delete(self, model):
        if len(Domain.query.all()) <= 1:
            raise ValidationError(f"at least one domain should exist")
        hiddify.flash_config_success(restart_mode='apply', domain_changed=True)
    def after_model_delete(self, model):
        if hconfig(ConfigEnum.parent_panel):
            hiddify_api.sync_child_to_parent()
    def after_model_change(self, form, model, is_created):
        if hconfig(ConfigEnum.parent_panel):
            hiddify_api.sync_child_to_parent()