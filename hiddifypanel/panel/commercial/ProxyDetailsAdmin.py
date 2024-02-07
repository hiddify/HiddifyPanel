from hiddifypanel.models import *
from hiddifypanel.panel.admin.adminlte import AdminLTEModelView
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from hiddifypanel.panel import hiddify
from flask import g
from hiddifypanel.auth import login_required
# Define a custom field type for the related domains

from flask import current_app


class ProxyDetailsAdmin(AdminLTEModelView):
    column_hide_backrefs = True
    can_create = False
    form_excluded_columns = ['child']
    column_exclude_list = ['child']
    column_searchable_list = ['name', 'proto', 'transport', 'l3', 'cdn']

    # list_template = 'model/domain_list.html'
    # edit_modal = True
    # form_overrides = {'work_with': Select2Field}

    def after_model_change(self, form, model, is_created):
        # if hconfig(ConfigEnum.parent_panel):
        #     hiddify_api.sync_child_to_parent()
        hiddify.get_available_proxies.invalidate_all()
        pass

    def after_model_delete(self, model):
        # if hconfig(ConfigEnum.parent_panel):
        #     hiddify_api.sync_child_to_parent()
        hiddify.get_available_proxies.invalidate_all()
        pass

    def is_accessible(self):
        if login_required(roles={Role.super_admin, Role.admin})(lambda: True)() != True:
            return False
        return True
