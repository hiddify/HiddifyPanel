from apiflask import HTTPBasicAuth, HTTPTokenAuth
from hiddifypanel.models.user import User, get_user_by_username, get_user_by_uuid
from hiddifypanel.models.admin import AdminUser, get_admin_by_username, get_admin_by_uuid

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
    user = User.query.filter(User.username == username, User.password == password).first()
    if user:
        return user
    return AdminUser.query.filter(AdminUser.username == username, AdminUser.password == password).first()


@api_auth.verify_token
def verify_api_auth_token(token) -> User | AdminUser | None:
    # for now, token is the same as uuid
    user = get_user_by_uuid(token)
    return user if user else get_admin_by_uuid(token)


# ADD ERROR HANDLING TO AUTHENTICATIONS
