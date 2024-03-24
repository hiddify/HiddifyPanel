from flask.views import MethodView
from flask import current_app as app
from apiflask import Schema, fields
from hiddifypanel.models import Child
from hiddifypanel.auth import login_required


class ChildStatusSchema(Schema):
    unique_id = fields.String(required=True, description="The child's unique id")


class ChildStatusOutputSchema(Schema):
    existance = fields.Boolean(required=True, description="Whether child exists")


class StatusApi(MethodView):
    decorators = [login_required(child_parent_auth=True)]

    @app.input(ChildStatusSchema, arg_name='data')  # type: ignore
    @app.output(ChildStatusOutputSchema)  # type: ignore
    def post(self, data):
        res = ChildStatusOutputSchema()
        res.existance = False  # type: ignore

        child = Child.query.filter(Child.unique_id == data['unique_id']).first()
        if child:
            res.existance = True  # type: ignore

        return res
