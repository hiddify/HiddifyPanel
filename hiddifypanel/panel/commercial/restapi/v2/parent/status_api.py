from flask.views import MethodView
from flask import current_app as app
from apiflask import Schema, fields

from hiddifypanel.models import Child, Role
from hiddifypanel.auth import login_required


class ChildStatusInputSchema(Schema):
    child_unique_id = fields.String(required=True, description="The child's unique id")


class ChildStatusOutputSchema(Schema):
    existance = fields.Boolean(required=True, description="Whether child exists")


class StatusApi(MethodView):
    decorators = [login_required({Role.super_admin})]

    @app.input(ChildStatusInputSchema, arg_name='data')  # type: ignore
    @app.output(ChildStatusOutputSchema)  # type: ignore
    def post(self, data):
        res = ChildStatusOutputSchema()
        res.existance = False  # type: ignore

        child = Child.query.filter(Child.unique_id == data['child_unique_id']).first()
        if child:
            res.existance = True  # type: ignore

        return res
