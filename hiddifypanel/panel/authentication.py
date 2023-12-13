from typing import Set
from apiflask import HTTPBasicAuth, HTTPTokenAuth
from hiddifypanel.models.user import User, get_user_by_uuid
from hiddifypanel.models.admin import AdminUser, get_admin_by_uuid
from flask import session
from strenum import StrEnum

basic_auth = HTTPBasicAuth()
api_auth = HTTPTokenAuth("ApiKey")


class AccountRole(StrEnum):
    user = 'user'
    admin = 'admin'
    super_admin = 'super_admin'
    agent = 'agent'


def set_authentication_in_session(account: User | AdminUser) -> None:
    session['account'] = {
        'uuid': account.uuid,
        'role': get_user_role(account),
        # 'username': res.username,
    }


def verify_from_session(roles: Set[AccountRole] = set()) -> User | AdminUser | None:
    if session.get('account'):
        if roles:
            if session['account']['role'] in roles:
                if AccountRole.user in roles:
                    return get_user_by_uuid(session['account']['uuid'])
                else:
                    return get_admin_by_uuid(session['account']['uuid'])
        else:
            if session['account']['role'] == AccountRole.user:
                return get_user_by_uuid(session['account']['uuid'])
            else:
                return get_admin_by_uuid(session['account']['uuid'])


@api_auth.get_user_roles
@basic_auth.get_user_roles
def get_user_role(user) -> AccountRole | None:
    '''Returns user/admin role
     Allowed roles are:
     - for user:
        - user
     - for admin:
        - super_admin
        - admin
        - agent
    '''
    if isinstance(user, User):
        return AccountRole.user
    elif isinstance(user, AdminUser):
        match user.mode:
            case 'super_admin':
                return AccountRole.super_admin
            case 'admin':
                return AccountRole.admin
            case 'agent':
                return AccountRole.agent


@basic_auth.verify_password
def verify_basic_auth_password(username, password, check_session=True, roles: Set[AccountRole] = set()) -> AdminUser | User | None:
    username = username.strip()
    password = password.strip()
    if username and password:
        account = None
        if roles:
            if AccountRole.user in roles:
                account = User.query.filter(User.username == username, User.password == password).first()
            else:
                account = AdminUser.query.filter(AdminUser.username == username, AdminUser.password == password).first()
        else:
            account = User.query.filter(User.username == username, User.password == password).first()
            if not account:
                account = AdminUser.query.filter(AdminUser.username == username, AdminUser.password == password).first()

        if account:
            if roles:
                if account.mode in roles:
                    set_authentication_in_session(account)
                    return account
            else:
                set_authentication_in_session(account)
                return account

    if check_session:
        account = verify_from_session(roles)
        if account:
            return account


@api_auth.verify_token
def verify_api_auth_token(token) -> User | AdminUser | None:
    # for now, token is the same as uuid
    user = get_user_by_uuid(token)
    return user if user else get_admin_by_uuid(token)


def standalone_verify(roles: Set[AccountRole]) -> bool:
    '''This funciton is for ModelView-based views authentication'''

    auth = basic_auth.get_auth()
    if auth:
        account = verify_basic_auth_password(auth.username, auth.password, check_session=False, roles=roles)
        if account:
            return True

    if verify_from_session(roles):
        return True
    return False

# ADD ERROR HANDLING TO AUTHENTICATIONS
