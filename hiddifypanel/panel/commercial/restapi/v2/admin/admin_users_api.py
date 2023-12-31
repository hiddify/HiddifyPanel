from flask import current_app as app
from flask import g
from apiflask import abort
from flask.views import MethodView
from hiddifypanel.panel.auth import login_required
from hiddifypanel.models.role import Role
from .admin_user_api import AdminSchema, has_permission
from hiddifypanel.models import AdminUser, get_admin_by_uuid
from hiddifypanel.panel import hiddify


class AdminUsersApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin})]

    @app.output(AdminSchema(many=True))
    def get(self):
        admins = AdminUser.query.filter(AdminUser.parent_admin_id == g.account.id).all() or abort(404, "WTF!")
        return [admin.to_dict() for admin in admins]  # type: ignore

    @app.input(AdminSchema, arg_name='data')
    @app.output(AdminSchema)
    def put(self, data):
        uuid = data.get('uuid') or abort(422, "Parameter issue: 'uuid'")
        admin = get_admin_by_uuid(uuid)

        # update check permission
        if admin:
            if not has_permission(admin):
                abort(403, "You don't have permission to access this admin")

        dbuser = hiddify.add_or_update_admin(**data)
        return dbuser.to_dict()
