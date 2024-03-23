from typing import List
from apiflask import Schema, abort, fields
from flask.views import MethodView
from sqlalchemy.orm import joinedload
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
    usages_data = fields.Nested(UsageDataSchema, many=True, required=True, description="The list of users and their usage(in bytes) and connected IPs")


class UsageApi(MethodView):
    decorators = [login_required(child_parent_auth=True)]

    @app.input(UsageSchema, arg_name='data')  # type: ignore
    @app.output(UsageDataSchema(many=True))  # type: ignore
    def put(self, data):
        child = Child.query.filter(Child.unique_id == data['unique_id']).first()
        if not child:
            abort(400, "The child does not exist")
        # parse request data
        child_usages_data = convert_usage_api_response_to_dict(data['usages_data'])
        parent_current_usages_data = convert_usage_api_response_to_dict(get_users_usage_data_for_api())

        increased_usages = self.__calculate_parent_increased_usages(child_usages_data, parent_current_usages_data)

        # add users usage
        if not all(u['usage'] == 0 for u in increased_usages.values()):
            add_users_usage_uuid(increased_usages, child.id)

        # make response
        res = self.__create_response()

        return res

    def __create_response(self) -> dict:
        res = [UsageDataSchema.from_dict(item) for item in get_users_usage_data_for_api()]
        return res  # type: ignore

    def __calculate_parent_increased_usages(self, child_usages_data: dict, parent_usages_data: dict) -> dict:
        res = {}
        for p_uuid, p_usage in parent_usages_data.items():
            if c_usage := child_usages_data.get(p_uuid):
                res[p_uuid] = {
                    'usage':  c_usage['usage'] - p_usage['usage'],
                    'ips': child_usages_data[p_uuid]['ips'],
                }
        return res


def convert_usage_api_response_to_dict(data: List[dict]) -> dict:
    converted = {}
    for i in data:
        converted[str(i['uuid'])] = {
            'usage': i['usage'],
            'ips': ','.join(i['ips']) if i['ips'] else ''
        }
    return converted


def get_users_usage_data_for_api() -> List[dict]:
    users = User.query.all()
    usages_data = [{'uuid': u.uuid, 'usage': u.current_usage, 'ips': u.ips} for u in users]
    return usages_data  # type: ignore
