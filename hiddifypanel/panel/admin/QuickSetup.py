import re
import flask_babel
import uuid
# from flask_babelex import lazy_gettext as _
from flask import render_template, g, request
from flask_babel import gettext as _
import wtforms as wtf
from flask_wtf import FlaskForm
from flask_bootstrap import SwitchField
from hiddifypanel.panel import hiddify
from flask_classful import FlaskView
from wtforms.validators import ValidationError
# from gettext import gettext as _

from hiddifypanel.models import Domain, DomainType, StrConfig, ConfigEnum, get_hconfigs
from hiddifypanel.database import db
from hiddifypanel.auth import login_required
from hiddifypanel import hutils
from hiddifypanel.models import *


class QuickSetup(FlaskView):
    decorators = [login_required({Role.super_admin})]

    def index(self):
        return render_template(
            'quick_setup.html', lang_form=get_lang_form(),
            form=get_quick_setup_form(),
            ipv4=hutils.network.get_ip_str(4),
            ipv6=hutils.network.get_ip_str(6),
            admin_link=admin_link(),
            show_domain_info=True)

    def post(self):
        if request.args.get('changepw') == "true":
            AdminUser.current_admin_or_owner().uuid = str(uuid.uuid4())
        set_hconfig(ConfigEnum.first_setup, False)
        quick_form = get_quick_setup_form()
        lang_form = get_lang_form()
        if lang_form.lang_submit.data:
            if lang_form.validate_on_submit():
                set_hconfig(ConfigEnum.lang, lang_form.admin_lang.data)
                set_hconfig(ConfigEnum.admin_lang, lang_form.admin_lang.data)
                set_hconfig(ConfigEnum.country, lang_form.country.data)

                flask_babel.refresh()
                hutils.flask.flash((_('quicksetup.setlang.success')), 'success')
            else:
                hutils.flask.flash((_('quicksetup.setlang.error')), 'danger')

            return render_template(
                'quick_setup.html', form=get_quick_setup_form(True),
                lang_form=get_lang_form(),
                admin_link=admin_link(),
                ipv4=hutils.network.get_ip_str(4),
                ipv6=hutils.network.get_ip_str(6),
                show_domain_info=False)

        if quick_form.validate_on_submit():
            Domain.query.filter(Domain.domain == f'{hutils.network.get_ip_str(4)}.sslip.io').delete()
            db.session.add(Domain(domain=quick_form.domain.data.lower(), mode=DomainType.direct))
            set_hconfig(ConfigEnum.block_iran_sites, quick_form.block_iran_sites.data)
            set_hconfig(ConfigEnum.decoy_domain, quick_form.decoy_domain.data)
            # hiddify.bulk_register_configs([
            #     # {"key": ConfigEnum.telegram_enable, "value": quick_form.enable_telegram.data == True},
            #     # {"key": ConfigEnum.vmess_enable, "value": quick_form.enable_vmess.data == True},
            #     # {"key": ConfigEnum.firewall, "value": quick_form.enable_firewall.data == True},
            #     {"key": ConfigEnum.block_iran_sites, "value": quick_form.block_iran_sites.data == True},
            #     # {"key":ConfigEnum.decoy_domain,"value":quick_form.decoy_domain.data}
            # ])

            from .Actions import Actions
            return Actions().reinstall(domain_changed=True)
        else:
            hutils.flask.flash(_('config.validation-error'), 'danger')
        return render_template(
            'quick_setup.html', form=quick_form, lang_form=get_lang_form(True),
            ipv4=hutils.network.get_ip_str(4),
            ipv6=hutils.network.get_ip_str(6),
            admin_link=admin_link(),
            show_domain_info=False)


def get_lang_form(empty=False):
    class LangForm(FlaskForm):
        admin_lang = wtf.SelectField(
            _("config.admin_lang.label"), choices=[("en", _("lang.en")), ("fa", _("lang.fa")), ("pt", _("lang.pt")), ("zh", _("lang.zh")), ("ru", _("lang.ru"))],
            description=_("config.admin_lang.description"),
            default=hconfig(ConfigEnum.admin_lang))
        # lang=wtf.SelectField(_("config.lang.label"),choices=[("en",_("lang.en")),("fa",_("lang.fa"))],description=_("config.lang.description"),default=hconfig(ConfigEnum.lang))
        country = wtf.SelectField(
            _("config.country.label"), choices=[("ir", _("Iran")), ("zh", _("China")), ("other", "Others")],
            description=_("config.country.description"),
            default=hconfig(ConfigEnum.country))
        lang_submit = wtf.SubmitField(_('Submit'))

    return LangForm(None)if empty else LangForm()


def get_quick_setup_form(empty=False):
    def get_used_domains():
        configs = get_hconfigs()
        domains = []
        for c in configs:
            if "domain" in c:
                domains.append(configs[c])
        for d in Domain.query.all():
            domains.append(d.domain)
        return domains

    class QuickSetupForm(FlaskForm):
        domain_regex = "^([A-Za-z0-9\\-\\.]+\\.[a-zA-Z]{2,})$"

        domain_validators = [
            wtf.validators.Regexp(domain_regex, re.IGNORECASE, _("config.Invalid domain")),
            validate_domain,
            wtf.validators.NoneOf([d.domain.lower() for d in Domain.query.all()], _("config.Domain already used")),
            wtf.validators.NoneOf([c.value.lower() for c in StrConfig.query.all() if "fakedomain" in c.key and c.key != ConfigEnum.decoy_domain], _("config.Domain already used"))]
        domain = wtf.StringField(
            _("domain.domain"),
            domain_validators,
            description=_("domain.description"),
            render_kw={
                "class": "ltr",
                "pattern": domain_validators[0].regex.pattern,
                "title": domain_validators[0].message,
                "required": "",
                "placeholder": "sub.domain.com"})
        # enable_telegram = SwitchField(_("config.telegram_enable.label"), description=_("config.telegram_enable.description"), default=hconfig(ConfigEnum.telegram_enable))
        # enable_firewall = SwitchField(_("config.firewall.label"), description=_("config.firewall.description"), default=hconfig(ConfigEnum.firewall))
        block_iran_sites = SwitchField(_("config.block_iran_sites.label"), description=_(
            "config.block_iran_sites.description"), default=hconfig(ConfigEnum.block_iran_sites))
        # enable_vmess = SwitchField(_("config.vmess_enable.label"), description=_("config.vmess_enable.description"), default=hconfig(ConfigEnum.vmess_enable))
        decoy_domain = wtf.StringField(_("config.decoy_domain.label"), description=_("config.decoy_domain.description"), default=hconfig(
            ConfigEnum.decoy_domain), validators=[wtf.validators.Regexp(domain_regex, re.IGNORECASE, _("config.Invalid domain")), hutils.flask.validate_domain_exist])
        submit = wtf.SubmitField(_('Submit'))

    return QuickSetupForm(None) if empty else QuickSetupForm()


def validate_domain(form, field):
    domain = field.data
    dip = hutils.network.get_domain_ip(domain)
    if dip is None:
        raise ValidationError(_("Domain can not be resolved! there is a problem in your domain"))

    myip = hutils.network.get_ip(4)
    if dip and myip != dip:
        raise ValidationError(_("Domain (%(domain)s)-> IP=%(domain_ip)s is not matched with your ip=%(server_ip)s which is required in direct mode", server_ip=myip, domain_ip=dip, domain=domain))


def admin_link():
    domains = get_panel_domains()
    return hiddify.get_account_panel_link(g.account, domains[0] if len(domains)else hutils.network.get_ip_str(4))
