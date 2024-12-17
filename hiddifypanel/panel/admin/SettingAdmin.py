import re
import flask_babel
import flask_babel
from flask_babel import lazy_gettext as _
# from flask_babelex import gettext as _
from flask import render_template, g  # type: ignore
from markupsafe import Markup

from hiddifypanel.hutils.flask import hurl_for
from flask import current_app as app
from hiddifypanel import hutils
from hiddifypanel.auth import login_required
import wtforms as wtf
from flask_bootstrap import SwitchField

# from gettext import gettext as _
from flask_classful import FlaskView
from flask_wtf import FlaskForm
from bleach import clean as bleach_clean, ALLOWED_TAGS as BLEACH_ALLOWED_TAGS
ALLOWED_TAGS = set([*BLEACH_ALLOWED_TAGS, "h1", "h2", "h3", "h4", "p"])


from hiddifypanel.models import BoolConfig, StrConfig, ConfigEnum, hconfig, ConfigCategory
from hiddifypanel.models import *
from hiddifypanel.database import db
from hiddifypanel.panel import hiddify, custom_widgets
from hiddifypanel import __version__
from hiddifypanel.cache import cache


class SettingAdmin(FlaskView):

    @login_required(roles={Role.super_admin})
    def index(self):
        form = get_config_form()
        return render_template('config.html', form=form)

    @login_required(roles={Role.super_admin})
    def post(self):
        set_hconfig(ConfigEnum.first_setup, False)
        form = get_config_form()
        reset_action = None
        if form.validate_on_submit():

            boolconfigs = BoolConfig.query.filter(BoolConfig.child_id == Child.current().id).all()
            bool_types = {c.key: 'bool' for c in boolconfigs}

            old_configs = get_hconfigs()
            changed_configs = {}

            for category, c_items in form.data.items():  # [c for c in ConfigEnum]:

                if isinstance(c_items, dict):
                    for k in ConfigEnum:
                        if k.name not in c_items:
                            continue
                        v = c_items[k.name]
                        if k.type == str:
                            if "_domain" in k or "_fakedomain" in k:
                                v = v.lower()
                            if k == ConfigEnum.warp_sites and 'https://' in v:
                                hutils.flask.flash(_("config.warp-https-domain-for-warp-site"), 'error')
                                return render_template('config.html', form=form)
                            if "port" in k:
                                for p in v.split(","):
                                    for k2, v2 in c_items.items():
                                        if "port" in k2 and k.name != k2 and p in v2:
                                            hutils.flask.flash(_("Port is already used! in") + f" {k2} {k}", 'error')
                                            return render_template('config.html', form=form)
                            if k == ConfigEnum.parent_panel and v != '':
                                # v=(v+"/").replace("/admin",'')
                                v = re.sub("(/admin/.*)", "/", v) + ("/" if not v.endswith("/") else "")

                        if old_configs[k] != v:
                            changed_configs[k] = v

                # print(cat,vs)

            merged_configs = {**old_configs, **changed_configs}
            if len(set([merged_configs[ConfigEnum.proxy_path], merged_configs[ConfigEnum.proxy_path_client], merged_configs[ConfigEnum.proxy_path_admin]])) != 3:
                hutils.flask.flash(_("ProxyPath is already used! use different proxy path"), 'error')  # type: ignore
                return render_template('config.html', form=form)

            # validate parent_panel value
            parent_apikey = ''
            if p_p := changed_configs.get(ConfigEnum.parent_panel):
                domain, proxy_path, uuid = hutils.flask.extract_parent_info_from_url(p_p)
                if not domain or not proxy_path or not uuid or not hutils.node.is_panel_active(domain, proxy_path, uuid):
                    hutils.flask.flash(_('parent.invalid-parent-url'), 'danger')  # type: ignore
                    return render_template('config.html', form=form)
                else:
                    set_hconfig(ConfigEnum.parent_domain, domain)
                    set_hconfig(ConfigEnum.parent_admin_proxy_path, proxy_path)
                    parent_apikey = uuid

            for k, v in changed_configs.items():
                # html inputs santitizing
                if k in {ConfigEnum.branding_title, ConfigEnum.branding_site, ConfigEnum.branding_freetext}:
                    v = bleach_clean(v, tags=ALLOWED_TAGS)
                set_hconfig(k, v, commit=False)

            db.session.commit()
            flask_babel.refresh()

            # set panel mode
            p_mode = hconfig(ConfigEnum.panel_mode)
            if p_mode != PanelMode.parent:
                if hconfig(ConfigEnum.parent_panel):
                    if p_mode == PanelMode.standalone:
                        set_hconfig(ConfigEnum.panel_mode, PanelMode.child)
                else:
                    if p_mode != PanelMode.standalone:
                        set_hconfig(ConfigEnum.panel_mode, PanelMode.standalone)

            cache.invalidate_all_cached_functions()
            # hutils.proxy.get_proxies.invalidate_all()
            from hiddifypanel.panel.commercial.telegrambot import register_bot
            register_bot(set_hook=True)

            # sync with parent if needed
            if hutils.node.is_child():
                if hutils.node.child.is_registered():
                    hutils.node.run_node_op_in_bg(hutils.node.child.sync_with_parent, *[hutils.node.child.SyncFields.hconfigs])
                else:
                    name = hconfig(ConfigEnum.unique_id)
                    parent_info = hutils.node.get_panel_info(hconfig(ConfigEnum.parent_domain), hconfig(ConfigEnum.parent_admin_proxy_path), parent_apikey)
                    if parent_info.get('version') != __version__:
                        hutils.flask.flash(_('node.diff-version'), 'danger')  # type: ignore
                    if not hutils.node.child.register_to_parent(name, parent_apikey, mode=ChildMode.remote):
                        hutils.flask.flash(_('child.register-failed'), 'danger')  # type: ignore
                    else:  # TODO: it's just for debuging
                        hutils.flask.flash(_('child.register-success'))  # type: ignore

            reset_action = hiddify.check_need_reset(old_configs)

            if old_configs[ConfigEnum.admin_lang] != hconfig(ConfigEnum.admin_lang):
                form = get_config_form()
        else:
            hutils.flask.flash(_('config.validation-error'), 'danger')  # type: ignore
            for field, errors in form.errors.items():
                for error in errors:
                    hutils.flask.flash(error, 'danger')  # type: ignore
            

        return reset_action or render_template('config.html', form=form)

    def get_babel_string(self):
        res = ""
        strconfigs = StrConfig.query.all()
        boolconfigs = BoolConfig.query.all()
        bool_types = {c.key: 'bool' for c in boolconfigs}

        configs = [*boolconfigs, *strconfigs]
        for cat in ConfigCategory:
            if cat == 'hidden':
                continue

            cat_configs = [c for c in configs if c.key.category == cat]

            for c in cat_configs:
                res += f'{{{{_("config.{c.key}.label")}}}} {{{{_("config.{c.key}.description")}}}}'

            res += f'{{{{_("config.{cat}.label")}}}}{{{{_("config.{cat}.description")}}}}'
        for c in ConfigEnum:
            res += f'{{{{_("config.{c}.label")}}}} {{{{_("config.{c}.description")}}}}'
        return res


def get_config_form():
    strconfigs = StrConfig.query.filter(StrConfig.child_id == Child.current().id).all()
    boolconfigs = BoolConfig.query.filter(BoolConfig.child_id == Child.current().id).all()
    bool_types = {c.key: 'bool' for c in boolconfigs}

    configs = [*boolconfigs, *strconfigs]
    configs_key = {k.key: k for k in configs}
    # categories=sorted([ c for c in {c.key.category:1 for c in configs}])
    # dict_configs={cat:[c for c in configs if c.category==cat] for cat in categories}

    class DynamicForm(FlaskForm):
        pass
    is_parent = hutils.node.is_parent()

    for cat in ConfigCategory:
        if cat == 'hidden':
            continue

        cat_configs = [c for c in ConfigEnum if c.category == cat and (not is_parent or c.show_in_parent)]
        if len(cat_configs) == 0:
            continue

        class CategoryForm(FlaskForm):
            class Meta:
                csrf = False
            description_for_fieldset = wtf.TextAreaField("", description=_(f'config.{cat}.description'), render_kw={"class": "d-none"})
        for c2 in cat_configs:
            if not (c2 in configs_key):
                continue
            c = configs_key[c2]
            if hutils.node.is_parent():
                if c.key == ConfigEnum.parent_panel:
                    continue
            extra_info = ''
            if c.key in bool_types:
                field = SwitchField(_(f'config.{c.key}.label'), default=c.value, description=_(f'config.{c.key}.description'))
            elif c.key == ConfigEnum.core_type:
                field = wtf.SelectField(_(f"config.{c.key}.label"),
                                        choices=[("xray", _("Xray")), ("singbox", _("SingBox"))],
                                        description=_(f"config.{c.key}.description"),
                                        default=hconfig(c.key))
            elif c.key == ConfigEnum.warp_mode:
                field = wtf.SelectField(_(f"config.{c.key}.label"),
                                        choices=[("disable", _("Disable")), ("all", _("All")), ("custom", _("Only Blocked and Local websites"))],
                                        description=_(f"config.{c.key}.description"),
                                        default=hconfig(c.key))

            elif c.key == ConfigEnum.lang or c.key == ConfigEnum.admin_lang:
                field = wtf.SelectField(
                    _(f"config.{c.key}.label"),
                    choices=[("en", _("lang.en")), ("fa", Markup(_("lang.fa"))), ("zh", _("lang.zh")), ("pt", _("lang.pt")), ("ru", _("lang.ru")), ("my", _("lang.my"))],
                    description=_(f"config.{c.key}.description"),
                    default=hconfig(c.key))
            elif c.key == ConfigEnum.country:
                field = wtf.SelectField(_(f"config.{c.key}.label"), choices=[
                    ("ir", _("Iran")), ("zh", _("China")), ("ru", _("Russia")), ("other", _("Others"))], description=_(f"config.{c.key}.description"), default=hconfig(c.key))
            elif c.key == ConfigEnum.package_mode:
                package_modes = [("release", _("Release")), ("beta", _("Beta"))]
                if hconfig(c.key) == "develop":
                    package_modes.append(("develop", _("Develop")))
                field = wtf.SelectField(_(f"config.{c.key}.label"), choices=package_modes, description=_(f"config.{c.key}.description"), default=hconfig(c.key))

            # the shadowsocks2022_method is hidden now, because it only has one option to choose
            # elif c.key == ConfigEnum.shadowsocks2022_method:
            #     field = wtf.SelectField(
            #         _(f"config.{c.key}.label"),
            #         choices=[
            #             ("2022-blake3-aes-256-gcm", "2022-blake3-aes-256-gcm"),
            #             # ("2022-blake3-chacha20-poly1305", "2022-blake3-chacha20-poly1305"),
            #         ],
            #         description=_(f"config.{c.key}.description"), default=hconfig(c.key))

            elif c.key == ConfigEnum.utls:
                field = wtf.SelectField(
                    _(f"config.{c.key}.label"),
                    choices=[
                        ("none", "None"), ("chrome", "Chrome"), ("edge", "Edge"), ("ios", "iOS"), ("android", "Android"),
                        ("safari", "Safari"), ("firefox", "Firefox"), ('random', 'random'), ('randomized', 'randomized')],
                    description=_(f"config.{c.key}.description"),
                    default=hconfig(c.key)
                )
            elif c.key == ConfigEnum.telegram_lib:
                # if hconfig(ConfigEnum.telegram_lib)=='python':
                #     continue6
                libs = [
                    ("erlang", _("lib.telegram.erlang")),
                    ("python", _("lib.telegram.python")),
                    ("tgo", _("lib.telegram.go")),
                    # ("orig", _("lib.telegram.orignal")),
                ]
                field = wtf.SelectField(_("config.telegram_lib.label"), choices=libs, description=_(
                    "config.telegram_lib.description"), default=hconfig(ConfigEnum.telegram_lib))
            elif c.key == ConfigEnum.mux_protocol:
                choices = [("smux", 'smux'), ("yamux", "yamux"), ("h2mux", "h2mux")]
                field = wtf.SelectField(_(f"config.{c.key}.label"), choices=choices, description=_(f"config.{c.key}.description"), default=hconfig(c.key))

            elif c.key == ConfigEnum.warp_sites:
                validators = [wtf.validators.Length(max=2048),
                              wtf.validators.Regexp(r'^(?:[\w.-]+\.\w+(?:\.\w+)?(?:\r?\n|$)|^$)', 0, _("config.invalid-pattern-for-warp-sites") + f' {c.key}')
                              ]
                render_kw = {'class': "ltr", 'maxlength': 2048}
                field = wtf.TextAreaField(_(f'config.{c.key}.label'), validators, default=c.value,
                                          description=_(f'config.{c.key}.description'), render_kw=render_kw)
            elif c.key == ConfigEnum.branding_freetext:
                validators = [wtf.validators.Length(max=2048)]
                render_kw = {'class': "ltr", 'maxlength': 2048}
                field = custom_widgets.CKTextAreaField(_(f'config.{c.key}.label'), validators, default=c.value,
                                                       description=_(f'config.{c.key}.description'), render_kw=render_kw)
            else:
                render_kw = {'class': "ltr"}
                validators = []
                if c.key == ConfigEnum.domain_fronting_domain:
                    validators.append(wtf.validators.Regexp("^([A-Za-z0-9\\-\\.]+\\.[a-zA-Z]{2,})|$", re.IGNORECASE, _("config.Invalid_domain")))
                    validators.append(hutils.flask.validate_domain_exist)
                elif '_domain' in c.key or "_fakedomain" in c.key:
                    validators.append(wtf.validators.Regexp("^([A-Za-z0-9\\-\\.]+\\.[a-zA-Z]{2,})$", re.IGNORECASE, _("config.Invalid_domain")))
                    validators.append(hutils.flask.validate_domain_exist)

                    if c.key != ConfigEnum.decoy_domain:
                        validators.append(wtf.validators.NoneOf([d.domain.lower() for d in Domain.query.all()], _("config.Domain_already_used")))
                        validators.append(wtf.validators.NoneOf(
                            [cc.value.lower() for cc in StrConfig.query.filter(StrConfig.child_id == Child.current().id).all() if cc.key != c.key and "fakedomain" in cc.key and cc.key != ConfigEnum.decoy_domain], _("config.Domain_already_used")))

                    render_kw['required'] = ""
                    if len(c.value) < 3:
                        c.value = hutils.network.get_random_domains(1)[0]

                # if c.key ==ConfigEnum.reality_short_ids:
                #     extra_info=f" <a target='_blank' href='{hurl_for('admin.Actions:get_some_random_reality_friendly_domain',test_domain=c.value)}'>"+_('Example Domains')+"</a>"
                # if c.key ==ConfigEnum.reality_server_names:
                #     validators.append(wtf.validators.Regexp("^([\w-]+\.)+[\w-]+(,\s*([\w-]+\.)+[\w-]+)*$",re.IGNORECASE,_("Invalid REALITY hostnames")))
                    # gauge width gate lamp weasel jaguar minute enough few attitude endorse situate usdt trc20 doge bep20 trx doge ltc bnb eth btc bnb
                    # enjoy control list debris chronic few door broken way negative daring life season recipe profit switch bitter casual frame aunt plate brush aerobic display

                if c.key == ConfigEnum.parent_panel:
                    validators.append(wtf.validators.Regexp("()|(http(s|)://([A-Za-z0-9\\-\\.]+\\.[a-zA-Z]{2,})/.*)", re.IGNORECASE, _("Invalid admin link")))
                if c.key == ConfigEnum.telegram_bot_token:
                    validators.append(wtf.validators.Regexp("()|^([0-9]{8,12}:[a-zA-Z0-9_-]{30,40})|$", re.IGNORECASE, _("config.Invalid_telegram_bot_token")))
                if c.key == ConfigEnum.branding_site:
                    validators.append(wtf.validators.Regexp(
                        "()|(http(s|)://([A-Za-z0-9\\-\\.]+\\.[a-zA-Z]{2,})/?.*)", re.IGNORECASE, _("config.Invalid_brand_link")))
                    # render_kw['required']=""

                if 'secret' in c.key:
                    validators.append(wtf.validators.Regexp(
                        "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", re.IGNORECASE, _('config.invalid_uuid')))
                    render_kw['required'] = ""

                if c.key == ConfigEnum.proxy_path:
                    validators.append(wtf.validators.Regexp("^[a-zA-Z0-9]*$", re.IGNORECASE, _("config.Invalid_proxy_path")))
                    render_kw['required'] = ""

                if 'port' in c.key:
                    if c.key in [ConfigEnum.http_ports, ConfigEnum.tls_ports]:
                        validators.append(wtf.validators.Regexp("^(\\d+)(,\\d+)*$", re.IGNORECASE, _("config.Invalid_port")))
                        render_kw['required'] = ""
                    else:
                        validators.append(wtf.validators.Regexp("^(\\d+)(,\\d+)*$|^$", re.IGNORECASE, _("config.Invalid_port")))
                    # validators.append(wtf.validators.Regexp("^(\d+)(,\d+)*$",re.IGNORECASE,_("config.port is required")))

                # tls tricks validations
                if c.key in [ConfigEnum.tls_fragment_size, ConfigEnum.tls_fragment_sleep, ConfigEnum.tls_padding_length, ConfigEnum.wireguard_noise_trick]:
                    validators.append(wtf.validators.Regexp("^\\d+-\\d+$", re.IGNORECASE, _("config.Invalid_The_pattern_is_number-number") + f' {c.key}'))
                # mux and hysteria validations
                if c.key in [ConfigEnum.hysteria_up_mbps, ConfigEnum.hysteria_down_mbps, ConfigEnum.mux_max_connections, ConfigEnum.mux_min_streams, ConfigEnum.mux_max_streams,
                             ConfigEnum.mux_brutal_down_mbps, ConfigEnum.mux_brutal_up_mbps]:
                    validators.append(wtf.validators.Regexp("^\\d+$", re.IGNORECASE, _("config.Invalid_it_should_be_a_number_only") + f' {c.key}'))

                for val in validators:
                    if hasattr(val, "regex"):
                        render_kw['pattern'] = val.regex.pattern
                        render_kw['title'] = val.message

                if c.key == ConfigEnum.reality_public_key and g.account.mode in [AdminMode.super_admin]:
                    extra_info = f" <a href='{hurl_for('admin.Actions:change_reality_keys')}'>{_('Change')}</a>"

                field = wtf.StringField(_(f'config.{c.key}.label'), validators, default=c.value,
                                        description=_(f'config.{c.key}.description') + extra_info, render_kw=render_kw)
            setattr(CategoryForm, f'{c.key}', field)

        multifield = wtf.FormField(CategoryForm, Markup('<i class="fa-solid fa-plus"></i>&nbsp' + _(f'config.{cat}.label')))

        setattr(DynamicForm, cat, multifield)

    setattr(DynamicForm, "submit", wtf.SubmitField(_('Submit')))

    return DynamicForm()
