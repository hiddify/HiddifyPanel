from flask.views import MethodView
from flask import current_app as app
from apiflask import abort
from hiddifypanel.models.user import get_user_by_uuid
from hiddifypanel.panel import hiddify
from hiddifypanel.drivers import user_driver
from hiddifypanel.models import User
from .user_api import UserSchema


class UsersApi(MethodView):
    decorators = [hiddify.admin]

    @app.output(UserSchema(many=True))
    def get(self):
        users = User.query.all() or abort(502, "WTF!")
        return [user.to_dict(False) for user in users]

    @app.input(UserSchema, arg_name="data")
    @app.output(UserSchema)
    def put(self, data):
        hiddify.add_or_update_user(**data)
        user = get_user_by_uuid(data['uuid']) or abort(502, "unknown issue! user is not added")
        user_driver.add_client(user)
        hiddify.quick_apply_users()
        return user.to_dict(False)
