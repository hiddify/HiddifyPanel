from hiddifypanel.models import *
from hiddifypanel.panel.admin.adminlte import AdminLTEModelView
from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _
from hiddifypanel.panel import hiddify
from flask import g
from hiddifypanel.panel.auth import login_required
# Define a custom field type for the related domains

from flask import current_app
import hiddifypanel.panel.auth as auth


class ProxyDetailsAdmin(AdminLTEModelView):
    column_hide_backrefs = True
    form_excluded_columns = ['child']
    column_exclude_list = ['child']
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

    def inaccessible_callback(self, name, **kwargs):
        return auth.redirect_to_login()  # type: ignore
