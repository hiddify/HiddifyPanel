from flask import render_template, request, jsonify, g
from flask_wtf.file import FileField, FileRequired
from flask_bootstrap import SwitchField
from flask_babel import gettext as _
from flask_classful import FlaskView
from urllib.parse import urlparse
from flask_wtf import FlaskForm
from datetime import datetime
import wtforms as wtf
import json


from hiddifypanel.auth import login_required
from hiddifypanel.panel import hiddify
from hiddifypanel.models import *
from hiddifypanel import hutils


class Backup(FlaskView):
    decorators = [login_required({Role.super_admin})]

    def index(self):
        return render_template('backup.html', restore_form=get_restore_form())

    # @route("/backupfile")
    def backupfile(self):
        response = jsonify(hiddify.dump_db_to_dict())
        domain = urlparse(request.base_url).hostname
        filename = f'hiddify-{domain}-{datetime.now()}.json'
        response.headers.add('Content-disposition', f'attachment; filename={filename}')

        return response

    def post(self):

        restore_form = get_restore_form()

        if restore_form.validate_on_submit():
            set_hconfig(ConfigEnum.first_setup, False)
            file = restore_form.restore_file.data
            if isinstance(file, list):
                file = file[0]
            json_data = json.load(file)
            hiddify.set_db_from_json(json_data,
                                     set_users=restore_form.enable_user_restore.data,
                                     set_domains=restore_form.enable_domain_restore.data,
                                     set_settings=restore_form.enable_config_restore.data,
                                     override_unique_id=False,
                                     override_child_unique_id=True,
                                     override_root_admin=restore_form.override_root_admin.data
                                     # replace_owner_admin=restore_form.override_root_admin.data,
                                     )

            # remove default user cause it's not needed (program users wanted)
            if default := User.by_id(1):
                default.remove()

            from flask_babel import refresh
            refresh()
            # return redirect(hutils.flask.hurl_for("admin.Actions:reinstall2"))
            from .Actions import Actions
            g.new_proxy_path = hconfig(ConfigEnum.proxy_path_admin)
            g.force_proxy_path = g.proxy_path
            return Actions().reinstall(complete_install=True, domain_changed=True)
            # # hutils.flask.flash_config_success(full_install=True)
        else:
            hutils.flask.flash(_('Config file is incorrect'), category='error')
        return render_template('backup.html', restore_form=restore_form)


def get_restore_form(empty=False):
    class RestoreForm(FlaskForm):
        restore_file = FileField(_("Restore File"), description=_("Restore File Description"), validators=[FileRequired()])
        enable_config_restore = SwitchField(_("Restore Settings"), description=_("Restore Settings description"), default=False)
        enable_user_restore = SwitchField(_("Restore Users"), description=_("Restore Users description"), default=False)
        enable_domain_restore = SwitchField(_("Restore Domain"), description=_("Restore Domain description"), default=False)
        override_root_admin = SwitchField(_("Override Root Admin"), description=_("It will override the root admin to the current user"), default=False)
        submit = wtf.fields.SubmitField(_('Submit'))

    return RestoreForm(None) if empty else RestoreForm()
