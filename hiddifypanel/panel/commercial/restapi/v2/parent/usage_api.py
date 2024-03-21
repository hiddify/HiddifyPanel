from typing import List
from apiflask import Schema, abort, fields
from flask.views import MethodView
from flask import current_app as app
from hiddifypanel.models import User, Child, Role
from hiddifypanel.panel.usage import add_users_usage_uuid
from hiddifypanel.auth import login_required


class UsageDataSchema(Schema):
    uuid = fields.UUID(required=True, desciption="The user uuid")
    usage = fields.Integer(required=True, description="The user usage in bytes")
    ips = fields.List(fields.String(required=True, description="The user connected IPs"))


class UsageSchema(Schema):
    unique_id = fields.UUID(required=True, desicription="The unique id")
    users_info = fields.Nested(UsageDataSchema, many=True, required=True, description="The list of users and their usage(in bytes) and connected IPs")


class UsageApi(MethodView):
    decorators = [login_required({Role.super_admin})]

    @app.output(UsageDataSchema(many=True))  # type: ignore
    def get(self):
        res = self.__create_response()
        return res

    @app.input(UsageSchema, arg_name='data')  # type: ignore
    @app.output(UsageDataSchema(many=True))  # type: ignore
    def put(self, data):
        child = Child.query.filter(Child.unique_id == data['unique_id']).first()
        if not child:
            abort(400, "The child does not exist")
        # parse request data
        usage_data = {}
        for d in data['users_info']:
            usage_data[str(d['uuid'])] = {
                'usage': d['usage'],
                'ips': ','.join(d['ips']) if d['ips'] else ''
            }

        # add users usage
        add_users_usage_uuid(usage_data, child.id)

        # make response
        res = self.__create_response()

        return res

    def __create_response(self) -> dict:
        res = [UsageDataSchema.from_dict(item) for item in get_users_usage_info_for_api()]
        return res  # type: ignore


def get_users_usage_info_for_api() -> dict:
    # TODO: get user needed fields in one command (uuid, current_usage, connected_ips)
    users = User.query.all()
    users_info = [{'uuid': u.uuid, 'usage': u.current_usage, 'ips': u.ips} for u in users]
    return users_info  # type: ignore
