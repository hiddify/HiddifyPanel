import re
from flask_admin.actions import action
import datetime
import uuid
from apiflask import abort
from flask_bootstrap import SwitchField, BooleanField
from flask_babel import gettext as __
from .adminlte import AdminLTEModelView
from wtforms.validators import NumberRange
from flask_babel import lazy_gettext as _
from flask import g, request  # type: ignore
from markupsafe import Markup
from sqlalchemy import desc, func

from hiddifypanel.hutils.flask import hurl_for
from wtforms.validators import Regexp, ValidationError
from flask import current_app

import hiddifypanel
from hiddifypanel.models import *
from hiddifypanel.drivers import user_driver
from hiddifypanel.panel import hiddify, custom_widgets
from hiddifypanel.auth import login_required
from hiddifypanel import hutils


class UserAdmin(AdminLTEModelView):
    column_default_sort = ('id', False)  # Sort by username in ascending order

    column_sortable_list = ["is_active", "name", "current_usage", 'mode', "remaining_days", "comment", 'last_online', "uuid", 'remaining_days']
    column_searchable_list = ["uuid", "name"]
    column_list = ["is_active", "name", "UserLinks", "current_usage", "remaining_days", "comment", 'last_online', 'mode', 'admin', "uuid"]
    column_editable_list = ["comment", "name", "uuid"]
    form_extra_fields = {
        'reset_days': SwitchField(_("Reset package days"), default=False),
        'reset_usage': SwitchField(_("Reset package usage"), default=False),
        # 'disable_user': SwitchField(_("Disable User"))
    }
    list_template = 'model/user_list.html'

    form_columns = ["name", "comment", "usage_limit", "reset_usage", "package_days", "reset_days", "mode", "uuid", "enable",]
    # form_excluded_columns = ['current_usage', 'monthly', 'telegram_id', 'last_online', 'expiry_time', 'last_reset_time', 'current_usage_GB',
    #  'start_date', 'added_by', 'admin', 'details', 'max_ips', 'ed25519_private_key', 'ed25519_public_key', 'username', 'password']
    page_size = 50
    # edit_modal=True
    # create_modal=True
    # column_display_pk = True
    # can_export = True
    # form_overrides = dict(monthly=SwitchField)
    form_overrides = {

        'start_date': custom_widgets.DaysLeftField,
        'mode': custom_widgets.EnumSelectField,
        'usage_limit': custom_widgets.UsageField
    }

    # form_overrides = dict(expiry_time=custom_widgets.DaysLeftField,last_reset_time=custom_widgets.LastResetField)
    form_widget_args = {
        'current_usage_GB': {'min': '0'},
        'usage_limit_GB': {'min': '0'},
        'current_usage': {'min': '0'},
        'usage_limit': {'min': '0'},

    }
    form_args = {
        'max_ips': {
            'validators': [NumberRange(min=3, max=10000)]
        },
        'mode': {'enum': UserMode},
        'uuid': {
            'validators': [Regexp(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', message=__("Should be a valid uuid"))]
            #     'label': 'First Name',
            #     'validators': [required()]
        }
        # ,
        # 'expiry_time':{
        # "":'%Y-%m-%d'
        # }
    }
    # column_labels={'uuid':_("user.UUID")}
    # column_filters=["usage_limit_GB","current_usage_GB",'admin','is_active']

    column_labels = {
        "Actions": _("actions"),
        "name": _("user.name"),
        "UserLinks": _("user.user_links"),
        "usage_limit": _("user.usage_limit_GB"),
        "monthly": _("Reset every month"),
        "mode": _("Mode"),
        "admin": _("Added by"),
        "current_usage": _("user.current_usage_GB"),
        "start_date": _("Start Date"),
        "remaining_days": _("user.expiry_time"),
        "last_reset_time": _("user.last_reset_time"),
        "uuid": _("user.UUID"),
        "comment": _("Note"),
        'last_online': _('Last Online'),
        "package_days": _('Package Days'),
        "max_ips": _('Max IPs'),
        "enable": _('Enable'),
        "is_active": _('Active'),

    }
    # can_set_page_size=True

    def search_placeholder(self):
        return f"{_('search')} {_('user.UUID')} {_('user.name')}"
    # def get_column_name(self,field):
    #         return "x"
    #  return column_labels[field]
    column_descriptions = dict(
        # name=_'just for remembering',
        # usage_limit_GB="in GB",
        # current_usage_GB="in GB"
        comment=_("Add some text that is only visible to you."),
        mode=_("user.define_mode"),
        last_reset_time=_("If monthly is enabled, the usage will be reset after 30 days from this date."),
        start_date=_("From when the user package will be started? Empty for start from first connection"),
        package_days=_("How many days this package should be available?")
    )
    # column_editable_list=["usage_limit_GB","current_usage_GB","expiry_time"]
    # form_extra_fields={
    #     'uuid': {'label_name':"D"}

    #     }

    # can_edit = False
    # def on_model_change(self, form, model, is_created):
    #     model.password = generate_password_hash(model.password)
    def _enable_formatter(view, context, model, name):
        if model.is_active:
            link = '<i class="fa-solid fa-circle-check text-success"></i> '
        elif len(model.devices):
            link = '<i class="fa-solid fa-users-slash text-danger" title="{_("Too many Connected IPs")}"></i>'
        else:
            link = '<i class="fa-solid fa-circle-xmark text-danger"></i> '

        if hconfig(ConfigEnum.telegram_bot_token):
            if model.telegram_id:
                link += f'<button class="btn hbtn bg-h-blue btn-xs " onclick="show_send_message({model.id})" ><i class="fa-solid fa-paper-plane"></i></button> '
            else:
                link += f'<button class="btn hbtn bg-h-grey btn-xs disabled"><i class="fa-solid fa-paper-plane"></i></button> '

        return Markup(link)

    # def _name_formatter(view, context, model, name):
    #     # print("model.telegram_id",model.telegram_id)

    def _ul_formatter(view, context, model, name):
        href = f'{hiddify.get_account_panel_link(model, request.host, is_https=True)}#{hutils.encode.unicode_slug(model.name)}'

        link = f"""<a target='_blank' class='share-link btn btn-xs btn-primary' data-copy='{href}' href='{href}'>
        <i class='fa-solid fa-arrow-up-right-from-square'></i>
        {_("Current Domain")} </a>"""

        domains = [d for d in Domain.get_domains() if d.domain != request.host]
        return Markup(link + " ".join([hiddify.get_html_user_link(model, d) for d in domains]))

    # def _usage_formatter(view, context, model, name):
    #     return round(model.current_usage_GB,3)

    def _usage_formatter(view, context, model, name):
        u = round(model.current_usage_GB, 3)
        t = round(model.usage_limit_GB, 3)
        rate = round(u * 100 / (t + 0.000001))
        state = "danger" if u >= t else ('warning' if rate > 80 else 'success')
        color = "#ff7e7e" if u >= t else ('#ffc107' if rate > 80 else '#9ee150')
        return Markup(f"""
        <div class="progress progress-lg position-relative" style="min-width: 100px;">
          <div class="progress-bar progress-bar-striped" role="progressbar" style="width: {rate}%;background-color: {color};" aria-valuenow="{rate}" aria-valuemin="0" aria-valuemax="100"></div>
              <span class='badge position-absolute' style="left:auto;right:auto;width: 100%;font-size:1em">{u} {_('user.home.usage.from')} {t} GB</span>

        </div>
        """)

    def _expire_formatter(view, context, model: User, name):
        remaining = model.remaining_days

        diff = datetime.timedelta(days=remaining)

        state = 'success' if diff.days > 7 else ('warning' if diff.days > 0 else 'danger')
        formated = hutils.convert.format_timedelta(diff)
        return Markup(f"<span class='badge badge-{state}'>{'*' if not model.start_date else ''} {formated} </span>")
        # return Markup(f"<span class='badge ltr badge-}'>{days}</span> "+_('days'))

    def _admin_formatter(view, context, model, name):
        return Markup(f"<a href='{hurl_for('flask.user.index_view',admin_id=model.added_by)}' class='btn btn-xs btn-default'>{model.admin.name}</a>")

    def _online_formatter(view, context, model, name):
        if not model.last_online:
            return Markup("-")
        diff = model.last_online - datetime.datetime.now()

        if diff.days < -1000:
            return Markup("-")
        if diff.total_seconds() > -60 * 2:
            return Markup(f"<span class='badge badge-success'>{_('Online')}</span>")
        state = "danger" if diff.days < -3 else ("success" if diff.days >= -1 else "warning")
        return Markup(f"<span class='badge badge-{state}'>{hutils.convert.format_timedelta(diff,granularity='min')}</span>")

        # return Markup(f"<span class='badge ltr badge-{'success' if days>7 else ('warning' if days>0 else 'danger') }'>{days}</span> "+_('days'))

    column_formatters = {
        # 'name': _name_formatter,
        'UserLinks': _ul_formatter,
        # 'uuid': _uuid_formatter,
        'current_usage': _usage_formatter,
        "remaining_days": _expire_formatter,
        'last_online': _online_formatter,
        'admin': _admin_formatter,

        "is_active": _enable_formatter
    }

    def on_model_delete(self, model):
        if len(User.query.all()) <= 1:
            raise ValidationError(f"at least one user should exist")
        user_driver.remove_client(model)
        # hutils.flask.flash_config_success()

    def is_accessible(self):
        if login_required(roles={Role.super_admin, Role.admin, Role.agent})(lambda: True)() != True:
            return False
        return True

    def on_form_prefill(self, form, id=None):
        # print("================",form._obj.start_date)
        if id is None or form._obj is None or form._obj.start_date is None:
            msg = _("Package not started yet.")
            # form.reset['class']="d-none"
            delattr(form, 'reset_days')
            delattr(form, 'reset_usage')
            # delattr(form,'disable_user')
        else:
            remaining = form._obj.remaining_days  # remaining_days(form._obj)
            relative_remaining = hutils.convert.format_timedelta(datetime.timedelta(days=remaining))
            msg = _("Remaining about %(relative)s, exactly %(days)s days", relative=relative_remaining, days=remaining)
            form.reset_days.label.text += f" ({msg})"
            usr_usage = f" ({_('user.home.usage.title')} {round(form._obj.current_usage_GB,3)}GB)"
            form.reset_usage.label.text += usr_usage
            form.reset_usage.data = False
            form.reset_days.data = False

            form.usage_limit.label.text += usr_usage

            # if form._obj.mode==UserMode.disable:
            #     delattr(form,'disable_user')
            # form.disable_user.data=form._obj.mode==UserMode.disable
            if form._obj.start_date:
                started = form._obj.start_date - datetime.date.today()
                msg = _("Started from %(relative)s", relative=hutils.convert.format_timedelta(started))
                form.package_days.label.text += f" ({msg})"
                if started.days <= 0:
                    exact_start = _("Started %(days)s days ago", days=-started.days)
                else:
                    exact_start = _("Will Start in %(days)s days", days=started.days)
                form.package_days.description += f" ({exact_start})"

    def get_edit_form(self):
        form = super().get_edit_form()
        # print(form.__dict__)
        # user=User.query.filter(User.uuid==form.uuid).first()
        # if user and user.start_date:
        #     form.reset = SwitchField("Reset")
        return form

    def on_model_change(self, form, model, is_created):
        model.max_ips = max(3, model.max_ips or 10000)
        if len(User.query.all()) % 4 == 0:
            hutils.flask.flash(('<div id="show-modal-donation"></div>'), ' d-none')
        if not re.match("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", model.uuid):
            raise ValidationError('Invalid UUID e.g.,' + str(uuid.uuid4()))
        if hasattr(form, 'reset_usage') and form.reset_usage.data:
            model.current_usage_GB = 0
        # if model.telegram_id and model.telegram_id != '0' and not re.match(r"^[1-9]\d*$", model.telegram_id):
        #     raise ValidationError('Invalid Telegram ID')
        # if form.disable_user.data:
        #     model.mode=UserMode.disable
        if hasattr(form, 'reset_days') and form.reset_days.data:
            model.start_date = None
        model.package_days = min(model.package_days, 10000)
        old_user = User.by_id(model.id)
        if not model.added_by or model.added_by == 1:
            model.added_by = g.account.id
        if not g.account.can_have_more_users():
            raise ValidationError(_('You have too much users! You can have only %(active)s active users and %(total)s users',
                                  active=g.account.max_active_users, total=g.account.max_users))
        if old_user and old_user.uuid != model.uuid:
            user_driver.remove_client(old_user)

        # generated automatically
        # if not model.ed25519_private_key:
        #     priv, publ = hutils.crypto.get_ed25519_private_public_pair()
        #     model.ed25519_private_key = priv
        #     model.ed25519_public_key = publ
        # if not model.wg_pk:
        #     model.wg_pk, model.wg_pub, model.wg_psk = hutils.crypto.get_wg_private_public_psk_pair()

        # model.expiry_time=datetime.date.today()+datetime.timedelta(days=model.expiry_time)
        # if model.current_usage_GB < model.usage_limit_GB:
        #     xray_api.add_client(model.uuid)
        # else:
        #     xray_api.remove_client(model.uuid)
        # hutils.flask.flash_config_success()

    def after_model_change(self, form, model, is_created):
        if hconfig(ConfigEnum.first_setup):
            set_hconfig(ConfigEnum.first_setup, False)
        user = User.query.filter(User.uuid == model.uuid).first() or abort(404)
        if user.is_active:
            user_driver.add_client(model)
        else:
            user_driver.remove_client(model)
        hiddify.quick_apply_users()

        if hutils.node.is_parent():
            hutils.node.run_node_op_in_bg(hutils.node.parent.request_childs_to_sync)

    def after_model_delete(self, model):
        user_driver.remove_client(model)
        hiddify.quick_apply_users()

        if hutils.node.is_parent():
            hutils.node.run_node_op_in_bg(hutils.node.parent.request_childs_to_sync)

    def get_list(self, page, sort_column, sort_desc, search, filters, page_size=50, *args, **kwargs):
        res = None
        self._auto_joins = {}
        # print('aaa',args, kwargs)
        if sort_column in ['remaining_days', 'is_active']:
            query = self.get_query()

            if search:
                from sqlalchemy import or_
                search_conditions = or_(self.model.name.contains(search), self.model.uuid == search)
                query = query.filter(search_conditions)

            data = query.all()
            count = len(data)
            data = sorted(data, key=lambda p: getattr(p, sort_column), reverse=sort_desc)

            # Applying pagination
            start = page * page_size
            end = start + page_size
            data = data[start: end]
            res = count, data
        else:
            res = super().get_list(page, sort_column, sort_desc, search=search, filters=filters, page_size=page_size, *args, **kwargs)
        return res

        # Override the default get_list method to use the custom sort function
        # query = self.session.query(self.model)
        # if self._sortable_columns:
        #     # print("sor",self._sortable_columns['remaining_days'])
        #     for column, direction in self._get_default_order():
        #         # if column == 'remaining_days':
        #         #     # Use the custom sort function for 'remaining_days'
        #         #     query = query.order_by(self.model.remaining_days.asc() if direction == 'asc' else self.model.remaining_days.desc())
        #         # else:
        #         # Use the default sort function for other columns
        #         query = query.order_by(getattr(self.model, column).asc() if direction == 'asc' else getattr(self.model, column).desc())
        # count = query.count()
        # data = query.all()
        # return count, data

        # Override get_query() to filter rows based on a specific condition

    def get_query(self):
        # Get the base query
        query = super().get_query()

        admin_id = int(request.args.get("admin_id") or g.account.id)
        if admin_id not in g.account.recursive_sub_admins_ids():
            abort(403)
        admin = AdminUser.query.filter(AdminUser.id == admin_id).first()
        if not admin:
            abort(403)

        query = query.filter(User.added_by.in_(admin.recursive_sub_admins_ids()))

        return query

    # Override get_count_query() to include the filter condition in the count query
    def get_count_query(self):
        # Get the base count query

        # query = self.session.query(func.count(User.id)).

        query = super().get_count_query()

        admin_id = int(request.args.get("admin_id") or g.account.id)
        if admin_id not in g.account.recursive_sub_admins_ids():
            abort(403)
        admin = AdminUser.query.filter(AdminUser.id == admin_id).first()
        if not admin:
            abort(403)

        query = query.filter(User.added_by.in_(admin.recursive_sub_admins_ids()))

        # admin_id=int(request.args.get("admin_id") or g.account.id)
        # if admin_id not in g.account.recursive_sub_admins_ids():
        #     abort(403)
        # admin=AdminUser.query.filter(AdminUser.id==admin_id).first()
        # if not admin:
        #     abort(403)

        return query
