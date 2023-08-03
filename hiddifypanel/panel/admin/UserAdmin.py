from flask_admin.contrib import sqla
from hiddifypanel.panel.database import db
import datetime
from hiddifypanel.models import *
from flask import Markup, g, request, url_for, abort
from wtforms.validators import Regexp, ValidationError
import re
import uuid
from hiddifypanel.drivers import user_driver
from .adminlte import AdminLTEModelView
# from gettext import gettext as _
from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _

from wtforms.validators import NumberRange


from hiddifypanel.panel import hiddify, custom_widgets
from hiddifypanel.panel.hiddify import flash
from wtforms.fields import StringField
from flask_bootstrap import SwitchField


class UserAdmin(AdminLTEModelView):
    column_sortable_list = ["name", "current_usage_GB", 'mode', "remaining_days", "comment", 'last_online', "uuid", 'remaining_days']
    column_searchable_list = [("uuid"), "name"]
    column_list = ["name", "UserLinks", "current_usage_GB", "remaining_days", "comment", 'last_online', 'mode', 'admin', "uuid"]
    form_extra_fields = {
        'reset_days': SwitchField(_("Reset package days")),
        'reset_usage': SwitchField(_("Reset package usage")),
        # 'disable_user': SwitchField(_("Disable User"))
    }
    list_template = 'model/user_list.html'
    form_excluded_columns = ['monthly', 'telegram_id', 'last_online', 'expiry_time', 'last_reset_time', 'current_usage_GB',
                             'start_date', 'added_by', 'admin', 'details', 'max_ips', 'ed25519_private_key', 'ed25519_public_key']
    page_size = 50
    # edit_modal=True
    # create_modal=True
    # column_display_pk = True
    # can_export = True
    # form_overrides = dict(monthly=SwitchField)
    form_overrides = {
        'start_date': custom_widgets.DaysLeftField,
        'mode': custom_widgets.EnumSelectField
    }

    # form_overrides = dict(expiry_time=custom_widgets.DaysLeftField,last_reset_time=custom_widgets.LastResetField)
    form_widget_args = {
        'current_usage_GB': {'min': '0'},
        'usage_limit_GB': {'min': '0'},

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
        "usage_limit_GB": _("user.usage_limit_GB"),
        "monthly": _("Reset every month"),
        "mode": _("Mode"),
        "admin": _("Added by"),
        "current_usage_GB": _("user.current_usage_GB"),
        "start_date": _("Start Date"),
        "remaining_days": _("user.expiry_time"),
        "last_reset_time": _("user.last_reset_time"),
        "uuid": _("user.UUID"),
        "comment": _("Note"),
        'last_online': _('Last Online'),
        "package_days": _('Package Days'),
        "max_ips": _('Max IPs'),
        "enable": _('Enable'),

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
        mode=_("Define the user mode. Should the usage reset every month?"),
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

    def _name_formatter(view, context, model, name):
        proxy_path = hconfig(ConfigEnum.proxy_path)
        # print("model.telegram_id",model.telegram_id)
        extra = ""
        if hconfig(ConfigEnum.telegram_bot_token) and model.telegram_id:
            extra = f'<button class="btn hbtn bg-h-blue btn-xs " onclick="show_send_message({model.id})" ><i class="fa-solid fa-paper-plane"></i></button> '

        link = ''
        if model.is_active:
            link = '<i class="fa-solid fa-circle-check text-success"></i> '
        elif len(model.ips):
            link = '<i class="fa-solid fa-users-slash text-danger" title="{_("Too many Connected IPs")}"></i>'
        else:
            link = '<i class="fa-solid fa-circle-xmark text-danger"></i> '

        link += f"<a target='_blank' href='/{proxy_path}/{model.uuid}/#{model.name}'>{model.name} <i class='fa-solid fa-arrow-up-right-from-square'></i></a>"
        return Markup(extra+link)

    def _ul_formatter(view, context, model, name):
        domains = get_panel_domains()
        return Markup(" ".join([hiddify.get_user_link(model.uuid, d, 'new', model.name) for d in domains]))

    def _uuid_formatter(view, context, model, name):
        return Markup(f"<span>{model.uuid}</span>")
    # def _usage_formatter(view, context, model, name):
    #     return round(model.current_usage_GB,3)

    def _usage_formatter(view, context, model, name):
        u = round(model.current_usage_GB, 3)
        t = round(model.usage_limit_GB, 3)
        rate = round(u*100/(t+0.000001))
        state = "danger" if u >= t else ('warning' if rate > 80 else 'success')
        color = "#ff7e7e" if u >= t else ('#ffc107' if rate > 80 else '#9ee150')
        return Markup(f"""
        <div class="progress progress-lg position-relative" style="min-width: 100px;">
          <div class="progress-bar progress-bar-striped" role="progressbar" style="width: {rate}%;background-color: {color};" aria-valuenow="{rate}" aria-valuemin="0" aria-valuemax="100"></div>
              <span class='badge position-absolute' style="left:auto;right:auto;width: 100%;font-size:1em">{u} {_('user.home.usage.from')} {t} GB</span>

        </div>
        """)

    def _expire_formatter(view, context, model, name):
        remaining = remaining_days(model)

        diff = datetime.timedelta(days=remaining)

        state = 'success' if diff.days > 7 else ('warning' if diff.days > 0 else 'danger')
        formated = hiddify.format_timedelta(diff)
        return Markup(f"<span class='badge badge-{state}'>{'*' if not model.start_date else ''} {formated} </span>")
        # return Markup(f"<span class='badge ltr badge-}'>{days}</span> "+_('days'))

    def _admin_formatter(view, context, model, name):
        return Markup(f"<a href='{url_for('flask.user.index_view',admin_id=model.added_by)}' class='btn btn-xs btn-default'>{model.admin.name}</a>")

    def _online_formatter(view, context, model, name):
        if not model.last_online:
            return Markup("-")
        diff = model.last_online-datetime.datetime.now()

        if diff.days < -1000:
            return Markup("-")
        if diff.total_seconds() > -60*2:
            return Markup(f"<span class='badge badge-success'>{_('Online')}</span>")
        state = "danger" if diff.days < -3 else ("success" if diff.days >= -1 else "warning")
        return Markup(f"<span class='badge badge-{state}'>{hiddify.format_timedelta(diff,granularity='min')}</span>")

        # return Markup(f"<span class='badge ltr badge-{'success' if days>7 else ('warning' if days>0 else 'danger') }'>{days}</span> "+_('days'))

    column_formatters = {
        'name': _name_formatter,
        'UserLinks': _ul_formatter,
        'uuid': _uuid_formatter,
        'current_usage_GB': _usage_formatter,
        "remaining_days": _expire_formatter,
        'last_online': _online_formatter,
        'admin': _admin_formatter
    }

    def on_model_delete(self, model):
        if len(User.query.all()) <= 1:
            raise ValidationError(f"at least one user should exist")
        user_driver.remove_client(model)
        # hiddify.flash_config_success()

    # def is_accessible(self):
    #     return g.is_admin

    def on_form_prefill(self, form, id=None):
        # print("================",form._obj.start_date)
        if id == None or form._obj is None or form._obj.start_date is None:
            msg = _("Package not started yet.")
            # form.reset['class']="d-none"
            delattr(form, 'reset_days')
            delattr(form, 'reset_usage')
            # delattr(form,'disable_user')
        else:
            remaining = remaining_days(form._obj)
            msg = _("Remaining: ") + hiddify.format_timedelta(datetime.timedelta(days=remaining))
            form.reset_days.label.text += f" ({msg})"
            usr_usage = f" ({_('user.home.usage.title')} {round(form._obj.current_usage_GB,3)}GB)"
            form.reset_usage.label.text += usr_usage
            form.usage_limit_GB.label.text += usr_usage

        # if form._obj.mode==UserMode.disable:
        #     delattr(form,'disable_user')
        # form.disable_user.data=form._obj.mode==UserMode.disable
        form.package_days.label.text += f" ({msg})"

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
            flash(('<div id="show-modal-donation"></div>'), ' d-none')
        if not re.match("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", model.uuid):
            raise ValidationError('Invalid UUID e.g.,' + str(uuid.uuid4()))

        if form.reset_usage.data:
            model.current_usage_GB = 0
        # if form.disable_user.data:
        #     model.mode=UserMode.disable
        if form.reset_days.data:
            model.start_date = None
        model.package_days = min(model.package_days, 10000)
        old_user = user_by_id(model.id)
        if not model.added_by:
            model.added_by = g.admin.id
        if not g.admin.can_have_more_users():
            raise ValidationError(_('You have too much users! You can have only %(active)s active users and %(total)s users',
                                  active=g.admin.max_active_users, total=g.admin.max_users))
        if old_user and old_user.uuid != model.uuid:
            user_driver.remove_client(old_user)
        if not model.ed25519_private_key:
            priv, publ = hiddify.get_ed25519_private_public_pair()
            model.ed25519_private_key = priv
            model.ed25519_public_key = publ
        # model.expiry_time=datetime.date.today()+datetime.timedelta(days=model.expiry_time)

        # if model.current_usage_GB < model.usage_limit_GB:
        #     xray_api.add_client(model.uuid)
        # else:
        #     xray_api.remove_client(model.uuid)
        # hiddify.flash_config_success()
    # def is_accessible(self):
    #     return is_valid()

    def after_model_change(self, form, model, is_created):

        user = User.query.filter(User.uuid == model.uuid).first()
        if is_user_active(user):
            user_driver.add_client(model)
        else:
            user_driver.remove_client(model)
        hiddify.quick_apply_users()

    def after_model_delete(self, model):
        user_driver.remove_client(model)

        hiddify.quick_apply_users()

    def get_list(self, page, sort_column, sort_desc, search, filters, *args, **kwargs):
        res = None
        # print('aaa',args, kwargs)
        if 'remaining_days' == sort_column:
            query = self.get_query()

            data = query.all()
            count = len(data)
            data = sorted(data, key=lambda p: p.remaining_days, reverse=sort_desc)
            res = count, data
        else:

            res = super().get_list(page, sort_column, sort_desc, search, filters, *args, **kwargs)
        return res

        # Override the default get_list method to use the custom sort function
        query = self.session.query(self.model)
        if self._sortable_columns:
            # print("sor",self._sortable_columns['remaining_days'])
            for column, direction in self._get_default_order():
                # if column == 'remaining_days':
                #     # Use the custom sort function for 'remaining_days'
                #     query = query.order_by(self.model.remaining_days.asc() if direction == 'asc' else self.model.remaining_days.desc())
                # else:
                # Use the default sort function for other columns
                query = query.order_by(getattr(self.model, column).asc() if direction == 'asc' else getattr(self.model, column).desc())
        count = query.count()
        data = query.all()
        return count, data

        # Override get_query() to filter rows based on a specific condition

    def get_query(self):
        # Get the base query
        query = super().get_query()

        admin_id = int(request.args.get("admin_id") or g.admin.id)
        if admin_id not in g.admin.recursive_sub_admins_ids():
            abort(403)
        admin = AdminUser.query.filter(AdminUser.id == admin_id).first()
        if not admin:
            abort(403)

        query = query.filter(User.added_by.in_(admin.recursive_sub_admins_ids()))

        return query

    # Override get_count_query() to include the filter condition in the count query
    def get_count_query(self):
        # Get the base count query
        query = self.get_query()
        from sqlalchemy import func

        query = query.session.query(func.count(User.id))
        # query = super().get_count_query()
        # admin_id=int(request.args.get("admin_id") or g.admin.id)
        # if admin_id not in g.admin.recursive_sub_admins_ids():
        #     abort(403)
        # admin=AdminUser.query.filter(AdminUser.id==admin_id).first()
        # if not admin:
        #     abort(403)

        return query
