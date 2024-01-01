from flask_classful import FlaskView, route
from hiddifypanel.panel.auth import login_required, current_user
from flask import redirect, request, g, url_for
from apiflask import abort
import hiddifypanel.panel.hiddify as hiddify
from hiddifypanel.models import Role


class LoginView(FlaskView):

    @route('/')
    @route('/<path1>')
    @route('/<path1>/')
    @route('/<path1>/<path2>')
    @route('/<path1>/<path2>/')
    @route('/<path1>/<path2>/<path3>')
    @route('/<path1>/<path2>/<path3>/')
    def index(self, path1, path2=None, path3=None):
        force_arg = request.args.get('force')
        redirect_arg = request.args.get('redirect')
        if not current_user.is_authenticated or (force_arg and not request.headers.get('Authorization')):
            abort(401, "Unauthorized")

        if redirect_arg:
            return redirect(redirect_arg)
        if hiddify.is_admin_proxy_path() and g.account.role in {Role.super_admin, Role.admin, Role.agent}:
            return redirect(url_for('admin.Dashboard:index'))

        if g.user_agent.browser and hiddify.is_client_proxy_path():
            return redirect(url_for('client.UserView:index'))
        from hiddifypanel.panel.user import UserView
        return UserView().auto_sub()
