from typing import List
from apiflask import Schema, fields
from flask.views import MethodView
from flask import current_app as app
from hiddifypanel.models.role import Role
from hiddifypanel.models.user import User
from hiddifypanel.panel.usage import add_users_usage_uuid
from hiddifypanel.auth import login_required


class UsageDataSchema(Schema):
    uuid = fields.UUID(required=True, desciption="The user uuid")
    usage = fields.Float(required=True, description="The user usage in bytes")
    ips = fields.String(required=True, description="The user connected IPs")


class UsageSchema(Schema):
    unique_id = fields.UUID(required=True, desicription="The unique id")
    users_info = fields.Nested(UsageDataSchema, many=True, required=True, description="The list of users and their usage(in bytes) and connected IPs")


class UsageApi(MethodView):
    decorators = [login_required({Role.super_admin})]

    @app.input(UsageSchema, arg_name='data')  # type: ignore
    @app.output(UsageDataSchema(many=True))  # type: ignore
    def put(self, data):
        unique_id = data['unique_id']

        # parse request data
        usage_data = {}
        for d in data['users_info']:
            usage_data[d['uuid']] = {
                'usage': d['usage'],
                'ips': d['ips']
            }

        # add users usage
        add_users_usage_uuid(usage_data, unique_id)

        # make response
        res = self.__create_response()

        return res

    def __create_response(self) -> dict:
        res = [UsageDataSchema.from_dict(item) for item in get_users_usage_info_for_api()]
        return res  # type: ignore


def get_users_usage_info_for_api() -> dict:
    # TODO: get user needed fields in one command (uuid, current_usage, connected_ips)
    users = User.query.all()
    users_info = [{'uuid': u.uuid, 'usage': u.current_usage, 'ips': u.details.first().connected_ips} for u in users]
    return users_info  # type: ignore
