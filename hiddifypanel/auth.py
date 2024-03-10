
from flask import g, redirect, request, session
from hiddifypanel.hutils.flask import hurl_for
from flask_login.utils import _get_user
from functools import wraps
from hiddifypanel.models import *

from hiddifypanel import hutils
from werkzeug.local import LocalProxy
current_account: "BaseAccount" = LocalProxy(lambda: _get_user())


class AnonymousAccount(BaseAccount):
    __abstract__ = True

    @property
    def uuid(self):
        return None

    @property
    def lang(self) -> Lang | None:
        return None

    @property
    def role(self) -> Role | None:
        return None

    def get_id(self) -> str | None:
        return "-1"

    def __bool__(self):
        return False

    def __eq__(self, other):
        if other is None:
            return True
        if isinstance(other, AnonymousAccount):
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "AnonymousAccount"


def _get_user():
    if not g.get("__account_store", None):
        g.__account_store = AnonymousAccount()
    return g.__account_store


def admin_session_is_exist():
    return '_admin_id' in session


def logout_user():
    g.__account_store = None
    if '_user_id' in session:
        session.pop('_user_id')
    if '_admin_id' in session:
        session.pop('_admin_id')


def login_user(user: AdminUser | User, remember=False, duration=None, force=False, fresh=True):
    # abort(400, f'logining user: {user} {user.is_active}')
    g.__account_store = user
    # if not user.is_active:
    #     return False

    account_id = user.get_id()  # type: ignore
    # print('account_id', account_id)
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
            # print('xxxx', current_account)
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
    # return AdminUser.by_uuid(api_key) if is_admin else User.by_uuid(api_key)
    # api_key equals uuid for now
    return get_account_by_uuid(api_key, is_admin)


def get_account_by_uuid(uuid, is_admin):
    return AdminUser.by_uuid(f'{uuid}') if is_admin else User.by_uuid(f'{uuid}')


def login_by_uuid(uuid, is_admin: bool):
    account = get_account_by_uuid(uuid, is_admin)
    if not account:
        return False
    return login_user(account, force=True)


def auth_before_request():
    # print("before_request")
    account = None

    is_admin_path = hutils.flask.is_admin_proxy_path()
    next_url = None

    if g.uuid:
        # print("uuid", g.uuid, is_admin_path)
        account = get_account_by_uuid(g.uuid, is_admin_path)
        # print(account)
        if not account:
            return logout_redirect()

        next_url = request.url.replace(f'/{g.uuid}/', '/admin/' if is_admin_path else '/client/').replace("/admin/admin/",
                                                                                                          '/admin/').replace("http://", "https://")

    elif apikey := request.headers.get("Hiddify-API-Key"):
        account = get_account_by_api_key(apikey, is_admin_path)
        if not account:
            return logout_redirect()
    elif request.authorization:
        # print('request.authorization', request.authorization)
        uname = request.authorization.username
        pword = request.authorization.password
        if not pword:
            # print("NO PASSWORD so it is uuid")
            account = get_account_by_uuid(uname, is_admin_path)
        else:
            account = AdminUser.by_username_password(uname, pword) if is_admin_path else User.by_username_password(uname, pword)
        if not account:
            return logout_redirect()

    elif (session_user := session.get('_user_id')) and not is_admin_path:
        # print('session_user', session_user)
        account = User.by_id(int(session_user.split("_")[1]))  # type: ignore
        if not account:
            return logout_redirect()
    elif (session_admin := session.get('_admin_id')) and is_admin_path:
        # print('session_admin', session_admin)
        account = AdminUser.by_id(int(session_admin.split("_")[1]))  # type: ignore
        if not account:
            return logout_redirect()

    if account:
        g.__account_store = account
        # g.account_uuid = account.uuid
        g.is_admin = hutils.flask.is_admin_role(account.role)  # type: ignore
        login_user(account, force=True)
        # print("loggining in")
        if next_url is not None and g.user_agent['is_browser'] and ".webmanifest" not in request.path:
            return redirect(next_url)


def logout_redirect():
    print(f"Incorrect user {current_account}.... loggining out")
    logout_user()
    return redirect_to_login()


def redirect_to_login():
    # if g.user_agent['is_browser']:
    # return redirect(hurl_for('common_bp.LoginView:basic_0', force=1, next=request.path))
    return redirect(hurl_for('common_bp.LoginView:index', force=1, next=request.path))

    # else:
    #     abort(401, "Unauthorized")
    # return f'/{request.path.split("/")[1]}/?force=1&redirect={request.path}'

# @login_manager.request_loader
