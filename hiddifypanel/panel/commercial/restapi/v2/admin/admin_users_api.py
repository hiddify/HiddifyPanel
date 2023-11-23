from flask import current_app as app
from apiflask import abort
from flask.views import MethodView
from .admin_user_api import AdminSchema
from hiddifypanel.models import AdminUser
from hiddifypanel.panel import hiddify

class AdminUsersApi(MethodView):
    decorators = [hiddify.super_admin]

    @app.output(AdminSchema(many=True))
    def get(self):
        admins = AdminUser.query.all() or abort(502, "WTF!")
        return [admin.to_dict() for admin in admins]

    @app.input(AdminSchema, arg_name='data')
    @app.output(AdminSchema)
    def put(self, data):
        # data = request.json
        # uuid = data.get('uuid') or abort(422, "Parameter issue: 'uuid'")
        dbuser = hiddify.add_or_update_admin(**data)

        return dbuser.to_dict()