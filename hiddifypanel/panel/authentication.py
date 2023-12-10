from apiflask import HTTPBasicAuth, HTTPTokenAuth
from hiddifypanel.models import AdminUser, User
api_auth = HTTPTokenAuth("ApiKey")
basic_auth = HTTPBasicAuth()


@api_auth.verify_token
def verify_api_auth_token(token):
    # for now, token is the same as uuid
    user = User.query.filter(User.uuid == token).first()
    if user:
        return user
    else:
        return AdminUser.query.filter(AdminUser.uuid == token).first()


# @basic_auth.verify_password
# def verify_basic_auth_password(username, password):
#     user = User.query.filter(User.username == username).first()
#     if user and user.check_password(password):
#         return user
