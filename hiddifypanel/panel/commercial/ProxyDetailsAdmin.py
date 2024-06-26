from hiddifypanel.models import *
from hiddifypanel.panel.admin.adminlte import AdminLTEModelView
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from flask import g, redirect
from markupsafe import Markup
from hiddifypanel.auth import login_required
from flask_admin.actions import action
from flask_admin.contrib.sqla import form, filters as sqla_filters, tools
from flask_admin import expose


# Define a custom field type for the related domains
from hiddifypanel import hutils


class ProxyDetailsAdmin(AdminLTEModelView):
    list_template = 'model/proxydetail_list.html'
    column_hide_backrefs = True
    can_create = False
    form_excluded_columns = ['child', 'proto', 'transport', 'cdn']
    column_exclude_list = ['child']
    column_searchable_list = ['name', 'proto', 'transport', 'l3', 'cdn']
    column_editable_list = ['name']

    @expose('reset_proxies')
    def reset_proxies(self):
        from hiddifypanel.panel.init_db import get_proxy_rows_v1
        from hiddifypanel.database import db
        db.session.bulk_save_objects(get_proxy_rows_v1())
        db.session.commit()
        hutils.flask.flash((_('config.validation-success-no-reset')), 'success')  # type: ignore
        return redirect("./")

    @action('disable', 'Disable', 'Are you sure you want to disable selected proxies?')
    def action_disable(self, ids):
        query = tools.get_query_for_ids(self.get_query(), self.model, ids)
        count = query.update({'enable': False})

        self.session.commit()
        hutils.flask.flash(_('%(count)s records were successfully disabled.', count=count), 'success')
        hutils.proxy.get_proxies.invalidate_all()

    @action('enable', 'Enable', 'Are you sure you want to enable selected proxies?')
    def action_enable(self, ids):
        query = tools.get_query_for_ids(self.get_query(), self.model, ids)
        count = query.update({'enable': True})

        self.session.commit()
        hutils.flask.flash(_('%(count)s records were successfully enabled.', count=count), 'success')
        hutils.proxy.get_proxies.invalidate_all()

    # list_template = 'model/domain_list.html'

    # form_overrides = {'work_with': Select2Field}

    def after_model_change(self, form, model, is_created):
        if hutils.node.is_child():
            hutils.node.run_node_op_in_bg(hutils.node.child.sync_with_parent, *[hutils.node.child.SyncFields.proxies])
        hutils.proxy.get_proxies.invalidate_all()
        pass

    def after_model_delete(self, model):
        if hutils.node.is_child():
            hutils.node.run_node_op_in_bg(hutils.node.child.sync_with_parent, *[hutils.node.child.SyncFields.proxies])
        hutils.proxy.get_proxies.invalidate_all()
        pass

    def is_accessible(self):
        if login_required(roles={Role.super_admin, Role.admin})(lambda: True)() != True:
            return False
        return True

    def _enable_formatter(view, context, model, name):
        if model.enable:
            link = '<i class="fa-solid fa-circle-check text-success"></i> '
        else:
            link = '<i class="fa-solid fa-circle-xmark text-danger"></i> '
        return Markup(link)
    column_formatters = {

        "enable": _enable_formatter
    }
