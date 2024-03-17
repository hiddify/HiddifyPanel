from typing import List
from apiflask import Schema, fields
from flask.views import MethodView
from flask import current_app as app
from hiddifypanel.models.role import Role
from hiddifypanel.models.user import User
from hiddifypanel.panel import hiddify
from hiddifypanel.panel.usage import add_users_usage_uuid
from hiddifypanel.auth import login_required


class UsageDataSchema(Schema):
    uuid = fields.UUID(required=True, desciption="The user uuid")
    usage = fields.Float(required=True, description="The user usage in bytes")
    connected_ips = fields.String(required=True, description="The user connected IPs")


class UsageSchema(Schema):
    unique_id = fields.UUID(required=True, desicription="The unique id")
    users_info = fields.Nested(UsageDataSchema, many=True, required=True, description="The list of users and their usage(in bytes) and connected IPs")


class UsageApi(MethodView):
    decorators = [login_required({Role.super_admin})]

    @app.input(UsageSchema, arg_name='data')  # type: ignore
    @app.output(UsageDataSchema(many=True))  # type: ignore
    def put(self, data):
        unique_id = data['unique_id']
        users_info = data['users_info']

        # TODO: check with @hiddify that how we should update usage
        # # parse request data
        # users_usage:List[UsageDataSchema] = []
        # for u in data['users_info']:
        #     schema = UsageDataSchema()
        #     schema.uuid = u['uuid']
        #     schema.usage = u['usage']
        #     schema.connected_ips = u['connected_ips']
        #     users_usage.append(schema)

        # # add users usage
        # add_users_usage_uuid(users_usage,unique_id)

        # make response
        res = self.__create_response()

        return res

    def __create_response(self) -> dict:
        res = [UsageDataSchema.from_dict(item) for item in get_users_usage_info_for_api()]
        return res  # type: ignore


def get_users_usage_info_for_api() -> dict:
    # TODO: get user needed fields in one command (uuid, current_usage, connected_ips)
    users = User.query.all()
    users_info = [{'uuid': u.uuid, 'usage': u.current_usage, 'connected_ips': u.details.first().connected_ips} for u in users]
    return users_info  # type: ignore
