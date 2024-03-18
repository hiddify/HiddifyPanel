
from flask.views import MethodView
from flask import current_app as app
from apiflask import abort, Schema, fields

from hiddifypanel.models.user import User
from hiddifypanel.database import db
from hiddifypanel.models.child import Child
from hiddifypanel.models import *
from hiddifypanel.auth import login_required
from .register_api import DomainSchema, OutputUsersSchema, ProxySchema, HConfigSchema


class SyncDataSchema(Schema):
    # users = fields.List(fields.Nested(UserSchema),required=True,description="The list of users")
    domains = fields.List(fields.Nested(DomainSchema), required=True, description="The list of domains")
    proxies = fields.List(fields.Nested(ProxySchema), required=True, description="The list of proxies")
    # parent_domains = fields.List(fields.Nested(ParentDomainSchema),required=True,description="The list of parent domains")
    # admin_users = fields.List(fields.Nested(AdminSchema),required=True,description="The list of admin users")
    hconfigs = fields.List(fields.Nested(HConfigSchema), required=True, description="The list of configs")


class SyncSchema(Schema):
    panel_data = fields.Nested(SyncDataSchema, required=False, description="The child's data")
    unique_id = fields.String(required=False, description="The child's unique id")


class SyncApi(MethodView):
    decorators = [login_required({Role.super_admin})]

    @app.input(SyncSchema, arg_name='data')  # type: ignore
    @app.output(OutputUsersSchema)  # type: ignore
    def put(self, data):
        unique_id = data['unique_id']

        if not hconfig(ConfigEnum.is_parent):
            abort(400, "Not a parent")

        child = Child.query.filter(Child.unique_id == unique_id).first()
        if not child:
            abort(400, "The child does not exist")

        # TODO: insert data
        try:
            bulk_register_domains(data['panel_data']['domains'], commit=False, force_child_unique_id=child.unique_id)
            bulk_register_configs(data['panel_data']['hconfigs'], commit=False, froce_child_unique_id=child.unique_id)
            Proxy.bulk_register(data['panel_data']['proxies'], commit=False, force_child_unique_id=child.unique_id)
            db.session.commit()  # type: ignore
        except Exception as err:
            abort(400, str(err))

        return self.__create_response()

    def __create_response(self):
        '''Create response for parent register api'''
        res = OutputUsersSchema()
        res.users = [u.to_schema() for u in User.query.all()]  # type: ignore
        res.admin_users = [a.to_schema() for a in AdminUser.query.all()]  # type: ignore

        return res
