from flask_classful import FlaskView, route
from hiddifypanel.panel.auth import login_required, current_user, login_user
from flask import redirect, request, g, url_for, render_template, flash
from flask_babelex import lazy_gettext as _
from apiflask import abort
import hiddifypanel.panel.hiddify as hiddify
from hiddifypanel.models import Role
from hiddifypanel.models import *
from hiddifypanel.panel.user import UserView


class LoginView(FlaskView):

    # @route("/")
    def index(self, force=None, next=None):
        force_arg = request.args.get('force')
        redirect_arg = request.args.get('redirect')
        username_arg = request.args.get('user') or ''
        if not current_user.is_authenticated:
            return render_template('login.html', username=username_arg)

            # abort(401, "Unauthorized1")

        if redirect_arg:
            return redirect(redirect_arg)
        if hiddify.is_admin_proxy_path() and g.account.role in {Role.super_admin, Role.admin, Role.agent}:
            return redirect(url_for('admin.Dashboard:index'))
        if g.user_agent.browser and hiddify.is_client_proxy_path():
            return redirect(url_for('client.UserView:index'))

        from hiddifypanel.panel.user import UserView
        return UserView().auto_sub()

    @route('/<uuid:uuid>/<path:path>')
    @route('/<uuid:uuid>/')
    def uuid(self, uuid, path=''):
        proxy_path = hiddify.get_proxy_path_from_url(request.url)
        g.account = None
        uuid = str(uuid)
        if proxy_path == hconfig(ConfigEnum.proxy_path_client):
            g.account = User.by_uuid(uuid)
            path = f'client/{path}'
        elif proxy_path == hconfig(ConfigEnum.proxy_path_admin):
            g.account = AdminUser.by_uuid(uuid)
        if not g.account:
            abort(403)
        if not g.user_agent.browser and proxy_path == hconfig(ConfigEnum.proxy_path_client):
            userview = UserView()
            if "all.txt" in path:
                return userview.all_configs()
            if 'singbox.json' in path:
                return userview.singbox()
            if 'full-singbox.json' in path:
                return userview.full_singbox()
            if 'clash' in path:
                splt = path.split("/")
                meta_or_normal = 'meta' if splt[-2] == 'meta' else 'normal'
                typ = splt[-1].split('.yml')[0]
                return userview.clash_config(meta_or_normal=meta_or_normal, typ=typ)
            return userview.force_sub()

        login_user(g.account, force=True)

        return redirect(f"/{proxy_path}/{path}")

    @route("/l/")
    @route("/l")
    def basic(self):
        force_arg = request.args.get('force')
        redirect_arg = request.args.get('next')
        if not current_user.is_authenticated or (force_arg and not request.headers.get('Authorization')):
            username = request.authorization.username if request.authorization else ''

            loginurl = url_for('common_bp.LoginView:index', force=force, next=next, user=username)
            if g.user_agent.browser and request.headers.get('Authorization') or (auth.current_user and auth.current_user != username):
                flash(_('Incorrect Password'), 'error')
                # flash(request.authorization.username, 'error')
                return redirect(loginurl)
            return render_template("redirect.html", url=loginurl), 401
            # abort(401, "Unauthorized1")

        if redirect_arg:
            return redirect(redirect_arg)
        if hiddify.is_admin_proxy_path() and g.account.role in {Role.super_admin, Role.admin, Role.agent}:
            return redirect(url_for('admin.Dashboard:index'))

        if g.user_agent.browser and hiddify.is_client_proxy_path():
            return redirect(url_for('client.UserView:index'))
        from hiddifypanel.panel.user import UserView
        return UserView().auto_sub()

    @route('/manifest.webmanifest')
    @login_required()
    def create_pwa_manifest(self):
        domain = urlparse(request.base_url).hostname
        name = (domain if g.is_admin else g.user.name)
        return jsonify({
            "name": f"Hiddify {name}",
            "short_name": f"{name}"[:12],
            "theme_color": "#f2f4fb",
            "background_color": "#1a1b21",
            "display": "standalone",
            "scope": f"/",
            "start_url": hiddify.hutils.utils.add_basic_auth_to_url(f"https://{domain}/{g.proxy_path}/?pwa=true", g.account.username, g.account.password),
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
