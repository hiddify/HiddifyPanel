from flask import current_app as app
from flask import g
from apiflask import abort
from flask.views import MethodView
from hiddifypanel.auth import login_required
from hiddifypanel.models.role import Role
from .admin_user_api import AdminSchema
from hiddifypanel.models import AdminUser


class AdminUsersApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin})]

    @app.output(AdminSchema(many=True))  # type: ignore
    def get(self):
        admins = AdminUser.query.filter(AdminUser.id.in_(g.account.recursive_sub_admins_ids())).all() or abort(404, "You have no admin")
        return [admin.to_schema() for admin in admins]  # type: ignore
