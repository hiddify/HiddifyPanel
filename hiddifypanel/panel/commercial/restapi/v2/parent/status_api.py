from flask.views import MethodView
from flask import current_app as app

from hiddifypanel.models import Child, Role
from hiddifypanel.auth import login_required

from .schema import ChildStatusInputSchema, ChildStatusOutputSchema


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
