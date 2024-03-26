from flask.views import MethodView
from flask import current_app as app
from flask import g
from apiflask import Schema, fields

from hiddifypanel.models import Child, Role
from hiddifypanel.auth import login_required


class ChildStatusOutputSchema(Schema):
    existance = fields.Boolean(required=True, description="Whether child exists")


class StatusApi(MethodView):
    decorators = [login_required({Role.super_admin})]

    @app.output(ChildStatusOutputSchema)  # type: ignore
    def post(self):
        res = ChildStatusOutputSchema()
        res.existance = False  # type: ignore

        child = Child.query.filter(Child.unique_id == g.node_unique_id).first()
        if child:
            res.existance = True  # type: ignore

        return res
