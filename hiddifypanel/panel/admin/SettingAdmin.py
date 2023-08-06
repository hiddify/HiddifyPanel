import flask_babel
import flask_babelex
from hiddifypanel.models import BoolConfig, StrConfig, ConfigEnum, hconfig, ConfigCategory
from wtforms.validators import Regexp, ValidationError
from flask_babelex import lazy_gettext as _
# from flask_babelex import gettext as _
import wtforms as wtf
from flask_wtf import FlaskForm, CSRFProtect
from flask_bootstrap import SwitchField

from flask_admin.base import expose
# from gettext import gettext as _
from hiddifypanel.panel.hiddify import get_random_domains

import re
from flask import render_template, current_app, Markup, url_for, abort, g
from hiddifypanel.panel.hiddify import flash
from hiddifypanel.models import *
from hiddifypanel.panel.database import db
from wtforms.fields import *
from flask_classful import FlaskView
from hiddifypanel.panel import hiddify, custom_widgets


class SettingAdmin(FlaskView):

    @hiddify.super_admin
    def index(self):
        form = get_config_form()
        return render_template('config.html', form=form)

    @hiddify.super_admin
    def post(self):
        set_hconfig(ConfigEnum.first_setup, False)
        form = get_config_form()
        reset_action = None
        if form.validate_on_submit():

            boolconfigs = BoolConfig.query.filter(BoolConfig.child_id == 0).all()
            bool_types = {c.key: 'bool' for c in boolconfigs}
            old_configs = get_hconfigs()
            changed_configs = {}
            for cat, vs in form.data.items():  # [c for c in ConfigEnum]:

                if type(vs) is dict:
                    for k in ConfigEnum:
                        if k not in vs:
                            continue
                        v = vs[k]
                        if k.type() == str:
                            if "_domain" in k or "_fakedomain" in k:
                                v = v.lower()

                            if "port" in k:
                                for p in v.split(","):
                                    for k2, v2 in vs.items():
                                        if "port" in k2 and k != k2 and p in v2:
                                            flash(_("Port is already used! in")+f" {k2} {k}", 'error')
                                            return render_template('config.html', form=form)
                            if k == ConfigEnum.parent_panel and v != '':
                                # v=(v+"/").replace("/admin",'')
                                v = re.sub("(/admin/.*)", "/", v)

                                # try:
                                #     # if hiddify_api.sync_child_to_parent(v)['status'] != 200:
                                #     #     flash(_("Can not connect to parent panel!"), 'error')
                                #     #     return render_template('config.html', form=form)
                                # except:
                                #     flash(_("Can not connect to parent panel!"), 'error')
                                #     return render_template('config.html', form=form)
                            StrConfig.query.filter(StrConfig.key == k, StrConfig.child_id == 0).first().value = v
                        if old_configs[k] != v:
                            changed_configs[k] = v

                # print(cat,vs)

            merged_configs = {**old_configs, **changed_configs}
            # for k in [ConfigEnum.reality_server_names,ConfigEnum.reality_fallback_domain]:
            #     v=merged_configs[k]
            #     for d in v.split(","):
            #         if not d:continue
            #         if not hiddify.is_domain_reality_friendly(d):
            #             flash(_("Domain is not REALITY friendly!")+" "+d,'error')
            #             return render_template('config.html', form=form)
            #         hiddify.debug_flash_if_not_in_the_same_asn(d)
            # fallback=merged_configs[ConfigEnum.reality_fallback_domain]
            # for d in merged_configs[ConfigEnum.reality_server_names].split(","):
            #     if not hiddify.fallback_domain_compatible_with_servernames(fallback, d):
            #         flash(_("REALITY Fallback domain is not compaitble with server names!")+" "+d+" != "+fallback,'error')
            #         return render_template('config.html', form=form)
            for k, v in changed_configs.items():
                set_hconfig(k, v, 0, False)
            db.session.commit()
            flask_babel.refresh()
            flask_babelex.refresh()

            from hiddifypanel.panel.commercial.telegrambot import register_bot
            register_bot()
            # if hconfig(ConfigEnum.parent_panel):
            #     hiddify_api.sync_child_to_parent()
            reset_action = hiddify.check_need_reset(old_configs)
            # if :
            #     return reset_action

            if old_configs[ConfigEnum.admin_lang] != hconfig(ConfigEnum.admin_lang):
                form = get_config_form()
        else:
            flash(_('config.validation-error'), 'danger')

        return reset_action or render_template('config.html', form=form)

        # # form=HelloForm()
        # # # return render('config.html',form=form)
        # # return render_template('config.html',form=HelloForm())
        # form=get_config_form()
        # return render_template('config.html',form=form)

    def get_babel_string(self):
        res = ""
        strconfigs = StrConfig.query.all()
        boolconfigs = BoolConfig.query.all()
        bool_types = {c.key: 'bool' for c in boolconfigs}

        configs = [*boolconfigs, *strconfigs]
        for cat in ConfigCategory:
            if cat == 'hidden':
                continue

            cat_configs = [c for c in configs if c.key.category() == cat]

            for c in cat_configs:
                res += f'{{{{_("config.{c.key}.label")}}}} {{{{_("config.{c.key}.description")}}}}'

            res += f'{{{{_("config.{cat}.label")}}}}{{{{_("config.{cat}.description")}}}}'
        for c in ConfigEnum:
            res += f'{{{{_("config.{c}.label")}}}} {{{{_("config.{c}.description")}}}}'
        return res


def get_config_form():

    strconfigs = StrConfig.query.filter(StrConfig.child_id == 0).all()
    boolconfigs = BoolConfig.query.filter(BoolConfig.child_id == 0).all()
    bool_types = {c.key: 'bool' for c in boolconfigs}

    configs = [*boolconfigs, *strconfigs]
    configs_key = {k.key: k for k in configs}
    # categories=sorted([ c for c in {c.key.category():1 for c in configs}])
    # dict_configs={cat:[c for c in configs if c.category==cat] for cat in categories}

    class DynamicForm(FlaskForm):
        pass
    is_parent = hconfig(ConfigEnum.is_parent)

    for cat in ConfigCategory:
        if cat == 'hidden':
            continue

        cat_configs = [c for c in ConfigEnum if c.category() == cat and (not is_parent or c.show_in_parent())]

        if len(cat_configs) == 0:
            continue

        class CategoryForm(FlaskForm):
            description_for_fieldset = wtf.fields.TextAreaField("", description=_(f'config.{cat}.description'), render_kw={"class": "d-none"})
        for c2 in cat_configs:
            if not (c2 in configs_key):
                continue
            c = configs_key[c2]
            extra_info = ''
            if c.key in bool_types:
                field = SwitchField(_(f'config.{c.key}.label'), default=c.value, description=_(f'config.{c.key}.description'))
            elif c.key == ConfigEnum.core_type:
                field = wtf.fields.SelectField(_(f"config.{c.key}.label"), choices=[("xray", _("Xray")), ("singbox", _(
                    "SingBox"))], description=_(f"config.{c.key}.description"), default=hconfig(c.key))
            elif c.key == ConfigEnum.warp_mode:
                field = wtf.fields.SelectField(_(f"config.{c.key}.label"), choices=[("disable", _("Disable")), ("all", _("All")), ("custom", _(
                    "Only Blocked and Local websites"))], description=_(f"config.{c.key}.description"), default=hconfig(c.key))

            elif c.key == ConfigEnum.lang or c.key == ConfigEnum.admin_lang:
                field = wtf.fields.SelectField(_(f"config.{c.key}.label"), choices=[("en", _("lang.en")), ("fa", Markup(_("lang.fa"))), ("zh", _(
                    "lang.zh")), ("pt", _("lang.pt"))], description=_(f"config.{c.key}.description"), default=hconfig(c.key))
            elif c.key == ConfigEnum.country:
                field = wtf.fields.SelectField(_(f"config.{c.key}.label"), choices=[("ir", _("Iran")), ("zh", _(
                    "China")), ("other", _("Others"))], description=_(f"config.{c.key}.description"), default=hconfig(c.key))
            elif c.key == ConfigEnum.package_mode:
                field = wtf.fields.SelectField(_(f"config.{c.key}.label"), choices=[("release", _("Release")),
                                               ("develop", _("Develop"))], description=_(f"config.{c.key}.description"), default=hconfig(c.key))
            elif c.key == ConfigEnum.utls:
                field = wtf.fields.SelectField(_(f"config.{c.key}.label"), choices=[("none", "None"), ("chrome", "Chrome"), ("edge", "Edge"), ("ios", "iOS"), ("android", "Android"), (
                    "safari", "Safari"), ("firefox", "Firefox"), ('random', 'random'), ('randomized', 'randomized')], description=_(f"config.{c.key}.description"), default=hconfig(c.key))
            elif c.key == ConfigEnum.telegram_lib:
                # if hconfig(ConfigEnum.telegram_lib)=='python':
                #     continue6
                libs = [("python", _("lib.telegram.python")), ("tgo", _("lib.telegram.go")), ("orig", _("lib.telegram.orignal")), ("erlang", _("lib.telegram.erlang"))]
                field = wtf.fields.SelectField(_("config.telegram_lib.label"), choices=libs, description=_(
                    "config.telegram_lib.description"), default=hconfig(ConfigEnum.telegram_lib))
            elif c.key == ConfigEnum.branding_freetext:
                validators = [wtf.validators.Length(max=2048)]
                render_kw = {'class': "ltr", 'maxlength': 2048}
                field = custom_widgets.CKTextAreaField(_(f'config.{c.key}.label'), validators, default=c.value, description=_(f'config.{c.key}.description'), render_kw=render_kw)
            else:
                render_kw = {'class': "ltr"}
                validators = []
                if c.key == ConfigEnum.domain_fronting_domain:
                    validators.append(wtf.validators.Regexp("^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})|$", re.IGNORECASE, _("config.Invalid domain")))
                    validators.append(hiddify.validate_domain_exist)
                elif '_domain' in c.key or "_fakedomain" in c.key:
                    validators.append(wtf.validators.Regexp("^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})$", re.IGNORECASE, _("config.Invalid domain")))
                    validators.append(hiddify.validate_domain_exist)

                    if c.key != ConfigEnum.decoy_domain:
                        validators.append(wtf.validators.NoneOf([d.domain.lower() for d in Domain.query.all()], _("config.Domain already used")))
                        validators.append(wtf.validators.NoneOf([cc.value.lower() for cc in StrConfig.query.filter(StrConfig.child_id == 0).all(
                        ) if cc.key != c.key and "fakedomain" in cc.key and cc.key != ConfigEnum.decoy_domain], _("config.Domain already used")))
                    render_kw['required'] = ""
                    if len(c.value) < 3:
                        c.value = get_random_domains(1)[0]
                # if c.key ==ConfigEnum.reality_short_ids:
                #     extra_info=f" <a target='_blank' href='{url_for('admin.Actions:get_some_random_reality_friendly_domain',test_domain=c.value)}'>"+_('Example Domains')+"</a>"
                # if c.key ==ConfigEnum.reality_server_names:
                #     validators.append(wtf.validators.Regexp("^([\w-]+\.)+[\w-]+(,\s*([\w-]+\.)+[\w-]+)*$",re.IGNORECASE,_("Invalid REALITY hostnames")))
                    # gauge width gate lamp weasel jaguar minute enough few attitude endorse situate usdt trc20 doge bep20 trx doge ltc bnb eth btc bnb
                    # enjoy control list debris chronic few door broken way negative daring life season recipe profit switch bitter casual frame aunt plate brush aerobic display
                if c.key == ConfigEnum.parent_panel:
                    validators.append(wtf.validators.Regexp("()|(http(s|)://([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})/.*)", re.IGNORECASE, _("Invalid admin link")))
                if c.key == ConfigEnum.telegram_bot_token:
                    validators.append(wtf.validators.Regexp("()|^([0-9]{8,12}:[a-zA-Z0-9_-]{30,40})|$", re.IGNORECASE, _("config.Invalid telegram bot token")))
                if c.key == ConfigEnum.branding_site:
                    validators.append(wtf.validators.Regexp("()|(http(s|)://([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})/?.*)", re.IGNORECASE, _("config.Invalid brand link")))
                    # render_kw['required']=""

                if 'secret' in c.key:
                    validators.append(wtf.validators.Regexp(
                        "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", re.IGNORECASE, _('config.invalid uuid')))
                    render_kw['required'] = ""

                if c.key == ConfigEnum.proxy_path:
                    validators.append(wtf.validators.Regexp("^[a-zA-Z0-9]*$", re.IGNORECASE, _("config.Invalid proxy path")))
                    render_kw['required'] = ""

                if 'port' in c.key:
                    if c.key in [ConfigEnum.http_ports, ConfigEnum.tls_ports]:
                        validators.append(wtf.validators.Regexp("^(\d+)(,\d+)*$", re.IGNORECASE, _("config.Invalid port")))
                        render_kw['required'] = ""
                    else:
                        validators.append(wtf.validators.Regexp("^(\d+)(,\d+)*$|^$", re.IGNORECASE, _("config.Invalid port")))

                    # validators.append(wtf.validators.Regexp("^(\d+)(,\d+)*$",re.IGNORECASE,_("config.port is required")))

                for val in validators:
                    if hasattr(val, "regex"):
                        render_kw['pattern'] = val.regex.pattern
                        render_kw['title'] = val.message
                if c.key == ConfigEnum.reality_public_key and g.admin.mode in [AdminMode.super_admin]:
                    extra_info = f" <a href='{url_for('admin.Actions:change_reality_keys')}'>{_('Change')}</>"
                field = wtf.fields.StringField(_(f'config.{c.key}.label'), validators, default=c.value,
                                               description=_(f'config.{c.key}.description')+extra_info, render_kw=render_kw)
            setattr(CategoryForm, c.key, field)

        multifield = wtf.fields.FormField(CategoryForm, Markup('<i class="fa-solid fa-plus"></i>&nbsp'+_(f'config.{cat}.label')))

        setattr(DynamicForm, cat,  multifield)

    setattr(DynamicForm, "submit", wtf.fields.SubmitField(_('Submit')))

    return DynamicForm()
