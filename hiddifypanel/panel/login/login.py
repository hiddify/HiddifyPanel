from flask_classful import FlaskView, route
from hiddifypanel.panel.auth import login_required, current_user
from flask import redirect, request, g, url_for, render_template, flash
from flask_babelex import lazy_gettext as _
from apiflask import abort
import hiddifypanel.panel.hiddify as hiddify
from hiddifypanel.models import Role


class LoginView(FlaskView):

    # @route("/")
    def index(self, force=None, next=None):
        force_arg = request.args.get('force')
        redirect_arg = request.args.get('redirect')
        username_arg = request.args.get('user')
        if not current_user.is_authenticated or (force_arg and not request.headers.get('Authorization')):
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

    @route("/l/")
    @route("/l")
    def basic(self, force=None, next=None):
        force_arg = force or request.args.get('force')
        redirect_arg = redirect or request.args.get('redirect')
        if not current_user.is_authenticated or (force_arg and not request.headers.get('Authorization')):
            username = request.authorization.username if request.authorization else ''
            nexturl = url_for('hlogin.LoginView:index', force=force, next=next, user=username)
            if request.headers.get('Authorization'):
                flash(_('Incorrect Password'), 'error')
                # flash(request.authorization.username, 'error')
                return redirect(nexturl)
            return render_template("redirect.html", url=nexturl), 401
            # abort(401, "Unauthorized1")

        if redirect_arg:
            return redirect(redirect_arg)
        if hiddify.is_admin_proxy_path() and g.account.role in {Role.super_admin, Role.admin, Role.agent}:
            return redirect(url_for('admin.Dashboard:index'))

        if g.user_agent.browser and hiddify.is_client_proxy_path():
            return redirect(url_for('client.UserView:index'))
        from hiddifypanel.panel.user import UserView
        return UserView().auto_sub()
