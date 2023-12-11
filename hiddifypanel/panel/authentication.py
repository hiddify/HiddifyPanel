from apiflask import HTTPBasicAuth, HTTPTokenAuth
from hiddifypanel.models.user import User, get_user_by_uuid
from hiddifypanel.models.admin import AdminUser, get_admin_by_uuid
from flask import session

basic_auth = HTTPBasicAuth()
api_auth = HTTPTokenAuth("ApiKey")


@api_auth.get_user_roles
@basic_auth.get_user_roles
def get_user_role(user) -> str | None:
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
        return 'user'
    elif isinstance(user, AdminUser):
        return str(user.mode)


@basic_auth.verify_password
def verify_basic_auth_password(username, password) -> str | None:
    if session.get('account'):
        if session['account']['role'] == 'user':
            return get_user_by_uuid(session['account']['uuid'])
        else:
            return get_admin_by_uuid(session['account']['uuid'])

    username = username.strip()
    password = password.strip()
    res = User.query.filter(User.username == username, User.password == password).first()
    if not res:
        res = AdminUser.query.filter(AdminUser.username == username, AdminUser.password == password).first()

    if res:
        session['account'] = {
            'uuid': res.uuid,
            'role': get_user_role(res),
            # 'username': res.username,
        }
    return res


@api_auth.verify_token
def verify_api_auth_token(token) -> User | AdminUser | None:
    # for now, token is the same as uuid
    user = get_user_by_uuid(token)
    return user if user else get_admin_by_uuid(token)


# ADD ERROR HANDLING TO AUTHENTICATIONS
