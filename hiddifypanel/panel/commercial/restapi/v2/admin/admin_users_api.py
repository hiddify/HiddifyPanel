from flask import current_app as app
from flask import g
from apiflask import abort
from flask.views import MethodView
from hiddifypanel.auth import login_required
from hiddifypanel.models.role import Role
from .admin_user_api import AdminSchema, has_permission
from hiddifypanel.models import AdminUser


class AdminUsersApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin})]

    @app.output(AdminSchema(many=True))  # type: ignore
    def get(self):
        admins = AdminUser.query.filter(AdminUser.id.in_(g.account.recursive_sub_admins_ids())).all() or abort(404, "You have no admin")
        return [admin.to_dict() for admin in admins]  # type: ignore

    @app.input(AdminSchema, arg_name='data')  # type: ignore
    @app.output(AdminSchema)  # type: ignore
    def put(self, data):
        uuid = data.get('uuid') or abort(422, "Parameter issue: 'uuid'")
        admin = AdminUser.by_uuid(uuid)  # type: ignore

        if not data.get('added_by_uuid'):
            data['added_by_uuid'] = g.account.uuid

        # update check permission
        if admin:
            if not has_permission(admin):
                abort(403, "You don't have permission to access this admin")

        dbadmin = AdminUser.add_or_update(**data) or abort(502, "Unknown issue: Admin is not added")
        return dbadmin.to_dict()  # type: ignore
