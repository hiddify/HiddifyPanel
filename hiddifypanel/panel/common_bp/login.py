from flask_classful import FlaskView, route
from hiddifypanel.panel.auth import login_required, current_account, login_user, logout_user, login_by_uuid
from flask import redirect, request, g, url_for, render_template, flash
from flask import current_app as app
from flask_babelex import lazy_gettext as _
from apiflask import abort
import hiddifypanel.panel.hiddify as hiddify
from hiddifypanel.models import Role
from hiddifypanel.models import *
from hiddifypanel.panel.user import UserView

from flask_wtf import FlaskForm
import wtforms as wtf
import re


class LoginForm(FlaskForm):
    secret_textbox = wtf.fields.StringField(_(f'login.secret.label'), [wtf.validators.Regexp(
        "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", re.IGNORECASE, _('config.invalid uuid'))], default='',
        description=_(f'login.secret.description'), render_kw={
        'required': "",
        'pattern': "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        'message': _('config.invalid uuid')
    })
    submit = wtf.fields.SubmitField(_('Submit'))


class LoginView(FlaskView):

    # @route("/")
    def index(self, force=None, next=None):
        force_arg = request.args.get('force')
        redirect_arg = request.args.get('redirect')
        username_arg = request.args.get('user') or ''
        if not current_account:

            return render_template('login.html', form=LoginForm())

            # abort(401, "Unauthorized1")

        if redirect_arg:
            return redirect(redirect_arg)
        if hiddify.is_admin_proxy_path() and g.account.role in {Role.super_admin, Role.admin, Role.agent}:
            return redirect(url_for('admin.Dashboard:index'))
        if g.user_agent['is_browser'] and hiddify.is_client_proxy_path():
            return redirect(url_for('client.UserView:index'))

        from hiddifypanel.panel.user import UserView
        return UserView().auto_sub()

    def post(self):
        form = LoginForm()
        if form.validate_on_submit():
            uuid = form.secret_textbox.data.strip()
            if login_by_uuid(uuid, hiddify.is_admin_proxy_path()):
                return redirect(f'/{g.proxy_path}/')
        flash(_('config.validation-error'), 'danger')
        return render_template('login.html', form=LoginForm())

    @route("/l/")
    @route("/l")
    def basic(self):
        redirect_arg = request.args.get('next')
        if not current_account or (not request.headers.get('Authorization')):
            username = request.authorization.username if request.authorization else ''

            loginurl = url_for('common_bp.LoginView:index', next=redirect_arg, user=username)
            if g.user_agent['is_browser'] and request.headers.get('Authorization') or (current_account and len(username) > 0 and current_account.username != username):
                flash(_('Incorrect Password'), 'error')
                logout_user()
                g.account = None
                # flash(request.authorization.username, 'error')
                return redirect(loginurl)

            return render_template("redirect.html", url=loginurl), 401
            # abort(401, "Unauthorized1")
        if redirect_arg:
            return redirect(redirect_arg)

        if hiddify.is_admin_proxy_path() and g.account.role in {Role.super_admin, Role.admin, Role.agent}:
            return redirect(url_for('admin.Dashboard:index'))

        if g.user_agent['is_browser'] and hiddify.is_client_proxy_path():
            return redirect(url_for('client.UserView:index'))
        from hiddifypanel.panel.user import UserView
        return UserView().auto_sub()

    # @route('/<uuid:uuid>/<path:path>')
    # @route('/<uuid:uuid>/')

    # def uuid(self, uuid, path=''):
    #     proxy_path = hiddify.get_proxy_path_from_url(request.url)
    #     g.account = None
    #     uuid = str(uuid)
    #     if proxy_path == hconfig(ConfigEnum.proxy_path_client):
    #         g.account = User.by_uuid(uuid)
    #         path = f'client/{path}'
    #     elif proxy_path == hconfig(ConfigEnum.proxy_path_admin):
    #         g.account = AdminUser.by_uuid(uuid)
    #     if not g.account:
    #         abort(403)
    #     if not g.user_agent['is_browser'] and proxy_path == hconfig(ConfigEnum.proxy_path_client):
    #         userview = UserView()
    #         if "all.txt" in path:
    #             return userview.all_configs()
    #         if 'singbox.json' in path:
    #             return userview.singbox()
    #         if 'full-singbox.json' in path:
    #             return userview.full_singbox()
    #         if 'clash' in path:
    #             splt = path.split("/")
    #             meta_or_normal = 'meta' if splt[-2] == 'meta' else 'normal'
    #             typ = splt[-1].split('.yml')[0]
    #             return userview.clash_config(meta_or_normal=meta_or_normal, typ=typ)
    #         return userview.force_sub()

    #     login_user(g.account, force=True)

    #     return redirect(f"/{proxy_path}/{path}")

    @route('/manifest.webmanifest')
    @login_required()
    def create_pwa_manifest(self):
        domain = request.host
        name = (domain if hiddify.is_admin_panel_call() else g.account.name)
        return jsonify({
            "name": f"Hiddify {name}",
            "short_name": f"{name}"[:12],
            "theme_color": "#f2f4fb",
            "background_color": "#1a1b21",
            "display": "standalone",
            "scope": f"/",
            "start_url": hiddify.get_account_panel_link(g.account, domain) +"?pwa=true",
            "description": "Hiddify, for a free Internet",
            "orientation": "any",
            "icons": [
                {
                    "src": hiddify.static_url_for(filename='images/hiddify-dark.png'),
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "maskable any"
                }
            ]
        })
