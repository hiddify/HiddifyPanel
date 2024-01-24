
from flask import flash as flask_flash
from flask import url_for, Markup  # type: ignore
from flask_babelex import lazy_gettext as _


def flash(message: str, category: str = "message"):
    # print(message)
    return flask_flash(Markup(message), category)


def flash_config_success(restart_mode='', domain_changed=True):
    if restart_mode:
        url = url_for('admin.Actions:reinstall', complete_install=restart_mode == 'reinstall', domain_changed=domain_changed)
        apply_btn = f"<a href='{url}' class='btn btn-primary form_post'>" + \
            _("admin.config.apply_configs")+"</a>"
        flash((_('config.validation-success', link=apply_btn)), 'success')  # type: ignore
    else:
        flash((_('config.validation-success-no-reset')), 'success')  # type: ignore


def static_url_for(**values):
    orig = url_for("static", **values)
    return orig.split("user_secret")[0]
