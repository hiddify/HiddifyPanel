from flask_login import LoginManager, current_user, user_accessed, user_logged_in,  COOKIE_NAME, AUTH_HEADER_NAME
from flask import g, redirect, request, session
from flask_login.utils import _get_user
from flask import current_app
from functools import wraps
from apiflask import abort

from hiddifypanel.models import AdminUser, User, Role, AccountType
import hiddifypanel.panel.hiddify as hiddify
from hiddifypanel import hutils


class CustumLoginManager(LoginManager):
    def _load_user(self):
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

        user = None

        account_id = ''
        # Load user from Flask Session
        if hiddify.is_api_call(request.path):
            if hiddify.is_user_api_call():
                account_id = session.get("_user_id")
            else:
                account_id = session.get("_admin_id")
        elif hiddify.is_user_panel_call():
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
            if has_cookie:
                cookie = request.cookies[cookie_name]
                user = self._load_user_from_remember_cookie(cookie)
            elif self._request_callback:
                user = self._load_user_from_request(request)
            elif header_name in request.headers:
                header = request.headers[header_name]
                user = self._load_user_from_header(header)

        return self._update_request_context_with_user(user)


def login_user(user: AdminUser | User, remember=False, duration=None, force=False, fresh=True):
    if not force and not user.is_active:
        return False

    account_id = getattr(user, current_app.login_manager.id_attribute)()  # type: ignore
    if user.role in {Role.super_admin, Role.admin, Role.agent}:
        session["_admin_id"] = account_id
    else:
        session["_user_id"] = account_id
    session["_fresh"] = fresh
    session["_id"] = current_app.login_manager._session_identifier_generator()  # type: ignore

    if remember:
        session["_remember"] = "set"
        if duration is not None:
            try:
                # equal to timedelta.total_seconds() but works with Python 2.6
                session["_remember_seconds"] = (
                    duration.microseconds
                    + (duration.seconds + duration.days * 24 * 3600) * 10**6
                ) / 10.0**6
            except AttributeError as e:
                raise Exception(
                    f"duration must be a datetime.timedelta, instead got: {duration}"
                ) from e

    current_app.login_manager._update_request_context_with_user(user)  # type: ignore
    user_logged_in.send(current_app._get_current_object(), user=_get_user())  # type: ignore
    return True


def login_required(roles: set[Role] | None = None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()  # type: ignore
            if roles:
                account_role = current_user.role
                if account_role not in roles:
                    return current_app.login_manager.unauthorized()  # type: ignore
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


def init_app(app):
    # login_manager = LoginManager()
    login_manager = CustumLoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def cookie_auth(id: str) -> User | AdminUser | None:
        if not hiddify.is_api_call(request.path):
            # if request.headers.get("Authorization"):
            #     return header_auth(request)
            # for handle new login
            if hiddify.is_login_call():
                return header_auth(request)

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

    @login_manager.request_loader
    def header_auth(request) -> User | AdminUser | None:
        auth_header: str = request.headers.get("Authorization")
        if not auth_header:
            return

        account = None
        is_api_call = False

        if hiddify.is_api_call(request.path):
            if apikey := hutils.utils.get_apikey_from_auth_header(auth_header):
                account = User.by_uuid(apikey) or AdminUser.by_uuid(apikey)
                is_api_call = True
        else:
            if username_password := hutils.utils.parse_basic_auth_header(auth_header):
                uname = username_password[0]
                pword = username_password[1]
                if hiddify.is_login_call():
                    account = AdminUser.by_username_password(uname, pword) if hiddify.is_admin_proxy_path() else User.by_username_password(uname, pword)
                elif hiddify.is_admin_panel_call():
                    account = AdminUser.by_username_password(uname, pword)
                elif hiddify.is_user_panel_call():
                    account = User.by_username_password(uname, pword)

        if account:
            g.account = account
            # g.account_uuid = account.uuid
            g.is_admin = hiddify.is_admin_role(account.role)  # type: ignore
            if not is_api_call:
                login_user(account)

        return account

    @login_manager.unauthorized_handler
    def unauthorized():
        # TODO: show the login page
        # return request.base_url
        if g.user_agent.browser:
            return redirect(f'/{request.path.split("/")[1]}/?force=1&redirect={request.path}')
        else:
            abort(401, "Unauthorized")
        # return f'/{request.path.split("/")[1]}/?force=1&redirect={request.path}'
