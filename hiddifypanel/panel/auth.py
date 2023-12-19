from flask_login import LoginManager, login_user
from hiddifypanel.models import User
import hiddifypanel.hutils as hutils
from flask import g, session
from hiddifypanel.models.admin import AdminUser, get_admin_by_uuid
from hiddifypanel.models.user import get_user_by_uuid
from hiddifypanel.hutils.utils import AccountRole


def init_app(app):
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def user_loader_auth(user_id) -> User | AdminUser | None:
        # check what type of account is stored in the session
        if role := session.get('account_role'):
            account = account = User.query.filter(User.id == user_id).first() if role == AccountRole.user else AdminUser.query.filter(AdminUser.id == user_id).first()
            if account:
                g.account = account
                g.account_uuid = account.uuid
                g.account_role = hutils.utils.get_account_role(account)
                g.is_admin = False if g.account_role == hutils.utils.AccountRole.user else True
            return account

    @login_manager.request_loader
    def request_loader_auth(request) -> User | AdminUser | None:
        auth_header: str = request.headers.get("Authorization")
        if not auth_header:
            return None

        account = None
        if 'api' in request.blueprint:
            if apikey := hutils.utils.get_apikey_from_auth_header(auth_header):
                account = get_user_by_uuid(apikey) or get_admin_by_uuid(apikey)
        else:
            if username_password := hutils.utils.parse_basic_auth_header(auth_header):
                if request.blueprint == 'user2':
                    account = User.query.filter(User.username == username_password[0], User.password == username_password[1]).first()
                else:
                    account = AdminUser.query.filter(AdminUser.username == username_password[0], AdminUser.password == username_password[1]).first()

        if account:
            g.account = account
            g.account_uuid = account.uuid
            account_role = hutils.utils.get_account_role(account)
            g.is_admin = False if account_role == hutils.utils.AccountRole.user else True

            # store user role to distict between user and admin
            session['account_role'] = account_role
            login_user(account)
        return account
