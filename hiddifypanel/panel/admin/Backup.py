#!/usr/bin/env python3
from urllib.parse import urlparse

from hiddifypanel.panel.database import db
import uuid
from flask_babelex import gettext as _
from flask_bootstrap import SwitchField
# from flask_babelex import gettext as _
import wtforms as wtf
from flask_wtf import FlaskForm
import pathlib
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
from datetime import datetime, timedelta, date
import os
import sys
import json
import urllib.request
import subprocess
import re
from hiddifypanel.panel import hiddify
from flask import current_app, render_template, request, Response, Markup, url_for, jsonify, redirect, g
from hiddifypanel.panel.hiddify import flash
from flask_wtf.file import FileField, FileRequired
import json

from flask_classful import FlaskView, route


class Backup(FlaskView):

    @hiddify.super_admin
    def index(self):
        return render_template('backup.html', restore_form=get_restore_form())

    # @route("/backupfile")
    @hiddify.super_admin
    def backupfile(self):
        response = jsonify(
            hiddify.dump_db_to_dict()
        )
        o = urlparse(request.base_url)
        domain = o.hostname
        response.headers.add('Content-disposition', f'attachment; filename=hiddify-{domain}-{datetime.now()}.json')

        return response

    @hiddify.super_admin
    def post(self):
        restore_form = get_restore_form()

        if restore_form.validate_on_submit():
            file = restore_form.restore_file.data
            json_data = json.load(file)

            hiddify.set_db_from_json(json_data,
                                     set_users=restore_form.enable_user_restore.data,
                                     set_domains=restore_form.enable_domain_restore.data,
                                     set_settings=restore_form.enable_config_restore.data,
                                     override_unique_id=False,
                                     override_child_id=None
                                     )

            from flask_babel import refresh
            refresh()
            return redirect(f'/{hconfig(ConfigEnum.proxy_path)}/{g.admin.uuid}/admin/actions/reinstall2/', code=302)
            from . import Actions
            action = Actions()
            return action.reinstall(complete_install=True, domain_changed=True)
            # hiddify.flash_config_success(full_install=True)
        else:
            flash(_('Config file is incorrect'))
        return render_template('backup.html', restore_form=restore_form)


def get_restore_form(empty=False):
    class RestoreForm(FlaskForm):
        restore_file = FileField(_("Restore File"), description=_("Restore File Description"), validators=[FileRequired()])
        enable_config_restore = SwitchField(_("Restore Settings"), description=_("Restore Settings description"), default=False)
        enable_user_restore = SwitchField(_("Restore Users"), description=_("Restore Users description"), default=False)
        enable_domain_restore = SwitchField(_("Restore Domain"), description=_("Restore Domain description"), default=False)
        submit = wtf.fields.SubmitField(_('Submit'))

    return RestoreForm(None) if empty else RestoreForm()
