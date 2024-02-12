from flask_login import LoginManager, current_user, user_accessed, user_logged_in, COOKIE_NAME, AUTH_HEADER_NAME, logout_user
from flask import g, redirect, request, session
from hiddifypanel.hutils.flask import hurl_for
from flask_login.utils import _get_user
from flask import current_app
from functools import wraps
from apiflask import abort

from hiddifypanel.models import AdminUser, User, Role, AccountType
import hiddifypanel.panel.hiddify as hiddify
from hiddifypanel import hutils


class CustumLoginManager(LoginManager):

    def _load_user(self):
        if hasattr(g, "account") and g.account:
            print(g.account)
            return g.account

        if self._user_callback is None and self._request_callback is None:
            raise Exception(
                "Missing user_loader or request_loader. Refer to "
                "http://flask-login.readthedocs.io/#how-it-works "
                "for more info."
            )

        user_accessed.send(current_app._get_current_object())  # type: ignore

        # Check SESSION_PROTECTION
        if self._session_protection_failed():
            return self._update_request_context_with_user()

        # user = self.header_auth()
        user = None

        account_id = ''
        # Load user from Flask Session
        if hutils.flask.is_api_call(request.path):
            if hutils.flask.is_user_api_call():
                account_id = session.get("_user_id")
            else:
                account_id = session.get("_admin_id")
        elif hutils.flask.is_user_panel_call():
            account_id = session.get("_user_id")
        else:
            account_id = session.get("_admin_id")

        if account_id is not None and self._user_callback is not None:
            user = self._user_callback(account_id)

        # Load user from Remember Me Cookie or Request Loader
        if user is None:
            config = current_app.config
            cookie_name = config.get("REMEMBER_COOKIE_NAME", COOKIE_NAME)
            header_name = config.get("AUTH_HEADER_NAME", AUTH_HEADER_NAME)
            has_cookie = (
                cookie_name in request.cookies and session.get("_remember") != "clear"
            )
            # if header_name in request.headers:
            #     header = request.headers[header_name]
            #     user = self._load_user_from_header(header)
            # if self._request_callback:
            #     user = self._load_user_from_request(request)
            if (cookie := request.cookies.get(cookie_name)):
                user = self._load_user_from_remember_cookie(cookie)

        return self._update_request_context_with_user(user)

    def header_auth(self) -> User | AdminUser | None:
        auth_header: str = request.headers.get("Authorization")
        print("DDDDDDDDDDDDD", auth_header)
        if not auth_header:
            return

        account = None
        is_api_call = False

        if hutils.flask.is_api_call(request.path):
            if apikey := hutils.auth.get_apikey_from_auth_header(auth_header):
                account = User.by_uuid(apikey) or AdminUser.by_uuid(apikey)
                is_api_call = True
        else:
            uname = request.authorization.username
            pword = request.authorization.password
            account = AdminUser.by_username_password(uname, pword) if hutils.flask.is_admin_proxy_path() else User.by_username_password(uname, pword)

        if account:
            g.account = account
            # g.account_uuid = account.uuid
            g.is_admin = hutils.flask.is_admin_role(account.role)  # type: ignore
            login_user(account)
        # else:
        #     print("logout")
        #     logout_user()

        return account


def login_user(user: AdminUser | User, remember=False, duration=None, force=False, fresh=True):
    g.account = user
    if not user.is_active:
        return False

    account_id = getattr(user, current_app.login_manager.id_attribute)()  # type: ignore
    if user.role in {Role.super_admin, Role.admin, Role.agent}:
        session["_admin_id"] = account_id
    else:
        session["_user_id"] = account_id
    session["_fresh"] = fresh
    session["_id"] = current_app.login_manager._session_identifier_generator()  # type: ignore

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

    current_app.login_manager._update_request_context_with_user(user)  # type: ignore
    user_logged_in.send(current_app._get_current_object(), user=_get_user())  # type: ignore
    return True


def login_required(roles: set[Role] | None = None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return auth.redirect_to_login()  # type: ignore
            if roles:
                account_role = current_user.role
                if account_role not in roles:
                    return auth.redirect_to_login()  # type: ignore
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


def get_account_by_api_key(api_key, is_admin):
    return AdminUser.by_uuid(api_key) if is_admin else User.by_uuid(api_key)


def get_account_by_uuid(uuid, is_admin):
    return AdminUser.by_uuid(uuid) if is_admin else User.by_uuid(uuid)


def init_app(app):
    # login_manager = LoginManager()
    login_manager = CustumLoginManager()
    login_manager.init_app(app)

    @app.before_request
    def auth_from_url():
        account = None

        is_admin_path = hutils.flask.is_admin_proxy_path()
        next_url = None
        print("--------1")
        if auth_header := request.headers.get("Authorization"):
            apikey = hutils.auth.get_apikey_from_auth_header(auth_header)
            account = get_account_by_api_key(apikey, is_admin_path)
            if not account:
                logout_user()

        if not account and (uuid := hutils.auth.get_uuid_from_url_path(request.path)):
            account = get_account_by_uuid(uuid, is_admin_path)
            if not account:
                logout_user()
            else:
                next_url = request.url.replace(f'/{uuid}/', '/' if is_admin_path else '/client/')
        print(request.authorization)
        if not account and request.authorization:
            uname = request.authorization.username
            pword = request.authorization.password
            account = AdminUser.by_username_password(uname, pword) if is_admin_path else User.by_username_password(uname, pword)
            print(request.authorization, account)
            if not account:
                logout_user()
        if account:
            g.account = account
            # g.account_uuid = account.uuid
            g.is_admin = hutils.flask.is_admin_role(account.role)  # type: ignore
            login_user(account, force=True)
            print("loggining in")
            if next_url is not None:
                if 0 and g.user_agent['is_browser']:
                    return redirect(next_url)
                else:
                    print(next_url)
                    request.url = next_url

    @login_manager.user_loader
    def cookie_auth(id: str) -> User | AdminUser | None:
        # if not hutils.flask.is_api_call(request.path):
        #     # if request.headers.get("Authorization"):
        #     #     return header_auth(request)
        #     # for handle new login
        #     if hutils.flask.is_login_call():
        #         # print("DDDDDDDDDDDDDDD-")
        #         return header_auth(request)

        # parse id
        acc_type, id = hutils.auth.parse_login_id(id)  # type: ignore
        if not acc_type or not id:
            return

        if acc_type == AccountType.admin:
            account = AdminUser.query.filter(AdminUser.id == id).first()
        else:
            account = User.query.filter(User.id == id).first()

        if account:
            g.account = account
            # g.account_uuid = account.uuid
            g.is_admin = hutils.flask.is_admin_role(account.role)
        return account

    @login_manager.unauthorized_handler
    def unauthorized():
        if g.user_agent['is_browser']:
            return redirect(hurl_for('common_bp.LoginView:basic_0', force=1, next={request.path}))

        else:
            abort(401, "Unauthorized")
        # return f'/{request.path.split("/")[1]}/?force=1&redirect={request.path}'

# @login_manager.request_loader
