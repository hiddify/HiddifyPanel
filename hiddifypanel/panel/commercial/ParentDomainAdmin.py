from flask_admin.contrib import sqla
from hiddifypanel.panel.database import db
from wtforms.validators import Regexp
from hiddifypanel.models import *
from wtforms.validators import Regexp, ValidationError
from hiddifypanel.panel.admin.adminlte import AdminLTEModelView
from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _
from hiddifypanel.panel import hiddify
from flask import Markup
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms import SelectMultipleField
from . import ParentDomain

from wtforms.widgets import ListWidget, CheckboxInput
from sqlalchemy.orm import backref
# Define a custom field type for the related domains
from flask_admin.form.fields import Select2TagsField, Select2Field


class ParentDomainAdmin(AdminLTEModelView):
    column_hide_backrefs = False

    list_template = 'model/domain_list.html'
    # edit_modal = True
    # form_overrides = {'work_with': Select2Field}

    column_descriptions = dict(
        domain=_("domain.description"),
        alias=_('The name shown in the configs for this domain.'),
        show_domains=_('You can select the configs with which domains show be shown in the user area. If you select all, automatically, all the new domains will be added for each users.')
        # current_usage_GB="in GB"
    )

    # create_modal = True
    can_export = False
    form_widget_args = {'show_domains': {'class': 'form-control ltr'}}
    form_args = {

        'domain': {
            'validators': [Regexp(r'^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})$', message=__("Should be a valid domain"))]
        },

    }
    column_list = ["domain", "alias", "show_domains_list"]
    # column_editable_list=["domain"]
    # column_filters=["domain","mode"]
    # form_excluded_columns=['work_with']
    column_searchable_list = ["domain"]
    column_labels = {
        "domain": _("domain.domain"),
        # "mode": _("domain.mode"),
        'alias': _('Alias'),
        'show_domains': _('Show Domains'),
        'show_domains_list': _('Show Domains')
    }

    form_columns = ['domain', "alias", 'show_domains']

    def _domain_admin_link(view, context, model, name):
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

    def _show_domains(view, context, model, name):
        # return Markup(f'<span class="badge badge-{badge_type}">{dip}</span>')
        res = ""
        for d in model.show_domains:
            res += f'<span class="badge">{d.domain}</span>'
        return Markup(res)

    column_formatters = {
        # 'domain_ip': _domain_ip,
        'domain': _domain_admin_link,
        'show_domains_list': _show_domains
    }

    def search_placeholder(self):
        return f"{_('search')} {_('domain.domain')}"

    # def on_form_prefill(self, form, id):
        # Get the Domain object being edited
        # domain = self.session.query(Domain).get(id)

        # Pre-select the related domains in the checkbox list
        # form.show_domains = [d.id for d in Domain.query.all()]

    def on_model_change(self, form, model, is_created):
        model.domain = model.domain.lower()

        dip = hiddify.get_domain_ip(model.domain)
        if dip == None:
            raise ValidationError(
                _("Domain can not be resolved! there is a problem in your domain"))
        # if not hiddify.check_connection_for_domain(model.domain):
        #     raise ValidationError(
        #         _("Domain is not correctly mapped to this server!"))
        print(model.show_domains)
        if len(model.show_domains) == Domain.query.count():
            model.show_domains = []

        hiddify.flash_config_success(restart_mode='apply', domain_changed=True)

    def on_model_delete(self, model):
        if len(ParentDomain.query.all()) <= 1:
            raise ValidationError(f"at least one domain should exist")
        hiddify.flash_config_success(restart_mode='apply', domain_changed=True)

    def is_accessible(self):
        return g.admin.mode in [AdminMode.admin, AdminMode.super_admin]
