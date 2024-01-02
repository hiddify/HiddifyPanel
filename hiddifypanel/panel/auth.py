from flask_login import LoginManager, current_user, user_accessed, user_logged_in,  COOKIE_NAME, AUTH_HEADER_NAME, logout_user
from flask import g, redirect, request, session, url_for
from flask_login.utils import _get_user
from flask import current_app
from functools import wraps
from apiflask import abort

from hiddifypanel.models import AdminUser, User, Role, AccountType
import hiddifypanel.panel.hiddify as hiddify
from hiddifypanel import hutils

from werkzeug.local import LocalProxy
current_account = LocalProxy(lambda: _get_user())


def _get_user():
    if not hasattr(g, "account"):
        g.account = None
    return g.account


def logout_user():
    g.account = None
    if '_user_id' in session:
        session.pop('_user_id')
    if '_admin_id' in session:
        session.pop('_admin_id')


def login_user(user: AdminUser | User, remember=False, duration=None, force=False, fresh=True):
    g.account = user
    if not user.is_active:
        return False

    account_id = user.get_id()  # type: ignore
    if user.role in {Role.super_admin, Role.admin, Role.agent}:
        session["_admin_id"] = account_id
    else:
        session["_user_id"] = account_id
    # session["_fresh"] = fresh
    # session["_id"] = current_app.login_manager._session_identifier_generator()  # type: ignore

    # if remember:
    #     session["_remember"] = "set"
    #     if duration is not None:
    #         try:
    #             # equal to timedelta.total_seconds() but works with Python 2.6
    #             session["_remember_seconds"] = (
    #                 duration.microseconds
    #                 + (duration.seconds + duration.days * 24 * 3600) * 10**6
    #             ) / 10.0**6
    #         except AttributeError as e:
    #             raise Exception(
    #                 f"duration must be a datetime.timedelta, instead got: {duration}"
    #             ) from e

    # current_app.login_manager._update_request_context_with_user(user)  # type: ignore
    # user_logged_in.send(current_app._get_current_object(), user=_get_user())  # type: ignore
    return True


def login_required(roles: set[Role] | None = None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_account:
                return redirect_to_login()  # type: ignore
            if roles:
                account_role = current_account.role
                if account_role not in roles:
                    return redirect_to_login()  # type: ignore
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


def get_account_by_api_key(api_key, is_admin):
    return AdminUser.by_uuid(api_key) if is_admin else User.by_uuid(api_key)


def get_account_by_uuid(uuid, is_admin):
    return AdminUser.by_uuid(uuid) if is_admin else User.by_uuid(uuid)


def init_app(app):
    # login_manager = LoginManager.()
    # login_manager = CustumLoginManager()
    # login_manager.init_app(app)

    @app.before_request
    def auth():
        account = None

        is_admin_path = hiddify.is_admin_proxy_path()
        next_url = None

        if auth_header := request.headers.get("Authorization"):
            apikey = hutils.utils.get_apikey_from_auth_header(auth_header)
            account = get_account_by_api_key(apikey, is_admin_path)
            if not account:
                logout_user()

        if not account and (uuid := hutils.utils.get_uuid_from_url_path(request.path)):
            account = get_account_by_uuid(uuid, is_admin_path)
            print("---------", account)
            if not account:
                logout_user()
            else:
                next_url = request.url.replace(f'/{uuid}/', '/' if is_admin_path else '/client/')

        if not account and request.authorization:
            uname = request.authorization.username
            pword = request.authorization.password
            account = AdminUser.by_username_password(uname, pword) if is_admin_path else User.by_username_password(uname, pword)
            print(request.authorization, account)
            if not account:
                logout_user()
        if not account and (session_user := session.get('_user_id')):
            account = User.by_id(int(session_user.split("_")[1]))  # type: ignore
            if not account:
                logout_user()
        if not account and (session_admin := session.get('_admin_id')):
            account = AdminUser.by_id(int(session_admin.split("_")[1]))  # type: ignore

        if account:
            g.account = account
            # g.account_uuid = account.uuid
            g.is_admin = hiddify.is_admin_role(account.role)  # type: ignore
            login_user(account, force=True)
            print("loggining in")
            if next_url is not None:
                if 0 and g.user_agent.browser:
                    return redirect(next_url)
                else:
                    request.url = next_url
                    return app.dispatch_request()

    # @login_manager.user_loader
    def cookie_auth(id: str) -> User | AdminUser | None:
        # if not hiddify.is_api_call(request.path):
        #     # if request.headers.get("Authorization"):
        #     #     return header_auth(request)
        #     # for handle new login
        #     if hiddify.is_login_call():
        #         # print("DDDDDDDDDDDDDDD-")
        #         return header_auth(request)

        # parse id
        acc_type, id = hutils.utils.parse_login_id(id)  # type: ignore
        if not acc_type or not id:
            return

        if acc_type == AccountType.admin:
            account = AdminUser.query.filter(AdminUser.id == id).first()
        else:
            account = User.query.filter(User.id == id).first()

        if account:
            g.account = account
            # g.account_uuid = account.uuid
            g.is_admin = hiddify.is_admin_role(account.role)
        return account

    # @login_manager.unauthorized_handler


def redirect_to_login():
    # TODO: show the login page
    # return request.base_url
    if g.user_agent.browser:
        return redirect(url_for('common_bp.LoginView:basic_0', force=1, next=request.path))

    else:
        abort(401, "Unauthorized")
        # return f'/{request.path.split("/")[1]}/?force=1&redirect={request.path}'

# @login_manager.request_loader
