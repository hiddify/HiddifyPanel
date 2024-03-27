
from flask.views import MethodView
from flask import current_app as app
from flask import g
from apiflask import abort, Schema, fields

from hiddifypanel.models.user import User
from hiddifypanel.database import db
from hiddifypanel.models.child import Child
from hiddifypanel.models import *
from hiddifypanel.auth import login_required
from .schema import *
from hiddifypanel import hutils


class SyncSchema(Schema):
    # users = fields.List(fields.Nested(UserSchema),required=True,description="The list of users")
    domains = fields.List(fields.Nested(DomainSchema), required=True, description="The list of domains")
    proxies = fields.List(fields.Nested(ProxySchema), required=True, description="The list of proxies")
    # parent_domains = fields.List(fields.Nested(ParentDomainSchema),required=True,description="The list of parent domains")
    # admin_users = fields.List(fields.Nested(AdminSchema),required=True,description="The list of admin users")
    hconfigs = fields.List(fields.Nested(HConfigSchema), required=True, description="The list of configs")


class SyncOutputSchema(Schema):
    users = fields.List(fields.Nested(UserSchema), required=True, description="The list of users")
    admin_users = fields.List(fields.Nested(AdminSchema), required=True, description="The list of admin users")


class SyncApi(MethodView):
    decorators = [login_required(node_auth=True)]

    @app.input(SyncSchema, arg_name='data')  # type: ignore
    @app.output(SyncOutputSchema)  # type: ignore
    def put(self, data):
        unique_id = g.node.unique_id

        if not hutils.node.is_parent():
            abort(400, "Not a parent")

        child = Child.query.filter(Child.unique_id == unique_id).first()
        if not child:
            abort(404, "The child does not exist")

        try:
            bulk_register_domains(data['domains'], commit=False, force_child_unique_id=child.unique_id)
            bulk_register_configs(data['hconfigs'], commit=False, froce_child_unique_id=child.unique_id)
            Proxy.bulk_register(data['proxies'], commit=False, force_child_unique_id=child.unique_id)
            db.session.commit()  # type: ignore
        except Exception as err:
            abort(400, str(err))

        res = SyncOutputSchema()
        res.users = [u.to_schema() for u in User.query.all()]  # type: ignore
        res.admin_users = [a.to_schema() for a in AdminUser.query.all()]  # type: ignore

        return res
