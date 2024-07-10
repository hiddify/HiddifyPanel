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
        """Admin: Get all admins"""
        admins = AdminUser.query.filter(AdminUser.id.in_(g.account.recursive_sub_admins_ids())).all() or abort(404, "You have no admin")
        return [admin.to_schema() for admin in admins]  # type: ignore

    @app.input(AdminSchema, arg_name='data')  # type: ignore
    @app.output(AdminSchema)  # type: ignore
    def post(self, data):
        """Admin: Create an admin"""
        if 'uuid' in data and AdminUser.by_uuid(data['uuid']):
            abort(400, "The admin exists")

        if not data.get('added_by_uuid'):
            data['added_by_uuid'] = g.account.uuid

        admin = AdminUser.add_or_update(**data) or abort(502, "Unknown issue: Admin is not added")
        return admin
