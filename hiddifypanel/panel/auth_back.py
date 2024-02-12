from typing import Set
from apiflask import HTTPBasicAuth, HTTPTokenAuth
from flask_httpauth import MultiAuth

from hiddifypanel.models.user import User
from hiddifypanel.models.admin import AdminUser
from flask import session
from strenum import StrEnum

basic_auth = HTTPBasicAuth()
api_auth = HTTPTokenAuth("ApiKey")
multi_auth = MultiAuth(basic_auth, api_auth)


class AccountRole(StrEnum):
    user = 'user'
    admin = 'admin'
    super_admin = 'super_admin'
    agent = 'agent'


@basic_auth.verify_password
def verify_basic_auth_password(username, password) -> AdminUser | User | None:
    # username = username.strip()
    # password = password.strip()
    if username and password:
        return User.query.filter(
            User.username == username, User.password == password).first() or AdminUser.query.filter(
            AdminUser.username == username, AdminUser.password == password).first()


@api_auth.verify_token
def verify_api_auth_token(token) -> User | AdminUser | None:
    # for now, token is the same as uuid
    # token = token.strip()
    if token:
        return User.by_uuid(token) or AdminUser.by_uuid(token)

    # we dont' set session for api auth
    # if check_session:Admin
    #     account = verify_from_session(roles)
    #     if account:
    #         return account


def set_admin_authentication_in_session(admin: AdminUser) -> None:
    if not session.get('account'):
        session['account'] = {
            'uuid': admin.uuid,
            'role': get_account_role(admin),
            # 'username': res.username,
        }


def set_user_authentication_in_session(user: User) -> None:
    session['user_sign'] = {'uuid': user.uuid}


def verify_admin_authentication_from_session() -> User | AdminUser | None:
    if session.get('account'):
        return User.by_uuid(session['account']['uuid']) or AdminUser.by_uuid(session['account']['uuid'])


def verify_user_authentication_from_session() -> User | AdminUser | None:
    if session.get('user_sign'):
        return User.by_uuid(session['user_sign']['uuid'])


# actually this is not used, we authenticate the client and setup it in
# the flask.g object, then in views we re-authenticate with their roles to
# see if they have access to the view or not
@api_auth.get_user_roles
@basic_auth.get_user_roles
def get_account_role(account) -> AccountRole | None:
    '''Returns user/admin role
     Allowed roles are:
     - for user:
        - user
     - for admin:
        - super_admin
        - admin
        - agent
    '''
    if isinstance(account, User):
        return AccountRole.user
    if isinstance(account, AdminUser):
        match account.mode:
            case 'super_admin':
                return AccountRole.super_admin
            case 'admin':
                return AccountRole.admin
            case 'agent':
                return AccountRole.agent


def standalone_admin_basic_auth_verification() -> AdminUser | None:
    auth = basic_auth.get_auth()

    if auth:
        account = verify_basic_auth_password(auth.username, auth.password)
        if account and isinstance(account, AdminUser):
            set_admin_authentication_in_session(account)
            return account

    return verify_admin_authentication_from_session()


def standalone_user_basic_auth_verification() -> User | None:
    auth = basic_auth.get_auth()

    if auth and auth.username and auth.password:
        user = verify_basic_auth_password(auth.username, auth.password)
        if user and isinstance(user, User):
            set_user_authentication_in_session(user)
            return user
    return verify_user_authentication_from_session()


def standalone_api_auth_verify():
    auth = api_auth.get_auth()
    try:
        if hasattr(auth, 'token'):
            account = verify_api_auth_token(auth.token)
            if account:
                return account
    except AttributeError:
        return None


# ADD ERROR HANDLING TO AUTHENTICATIONS
