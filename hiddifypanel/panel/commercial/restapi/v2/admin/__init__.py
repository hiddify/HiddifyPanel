from apiflask import APIBlueprint
from flask import g
from hiddifypanel.models import AdminUser, User

bp = APIBlueprint("api_admin", __name__, url_prefix="/<proxy_path>/api/v2/admin/", enable_openapi=True)


def init_app(app):

    with app.app_context():
        from .admin_info_api import AdminInfoApi
        from .server_status_api import AdminServerStatusApi
        from .admin_user_api import AdminUserApi
        from .admin_users_api import AdminUsersApi
        from .admin_log_api import AdminLogApi
        from .system_actions import UpdateUserUsageApi, AllConfigsApi
        bp.add_url_rule('/me/', view_func=AdminInfoApi)  # type: ignore
        bp.add_url_rule('/server_status/', view_func=AdminServerStatusApi)  # type: ignore
        bp.add_url_rule('/admin_user/<uuid:uuid>/', view_func=AdminUserApi)  # type: ignore
        bp.add_url_rule('/admin_user/', view_func=AdminUsersApi)  # type: ignore
        bp.add_url_rule('/log/', view_func=AdminLogApi)  # type: ignore
        bp.add_url_rule('/update_user_usage/', view_func=UpdateUserUsageApi)  # type: ignore
        bp.add_url_rule('/all-configs/', view_func=AllConfigsApi)  # type: ignore
        from .user_api import UserApi
        from .users_api import UsersApi
        bp.add_url_rule('/user/<uuid:uuid>/', view_func=UserApi)  # type: ignore
        bp.add_url_rule('/user/', view_func=UsersApi)  # type: ignore
    app.register_blueprint(bp)


def has_permission(model) -> bool:
    '''Check if the authenticated account has permission to do an action(get,insert,update,delete) on the another admin'''
    if g.account.uuid == AdminUser.get_super_admin_uuid():
        return True
    if isinstance(model, AdminUser) and model.parent_admin_id == g.account.id:
        return True
    elif isinstance(model, User) and model.added_by == g.account.id:
        return True

    return False
