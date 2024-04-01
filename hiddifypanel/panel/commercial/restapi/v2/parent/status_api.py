from flask.views import MethodView
from flask import current_app as app
from loguru import logger

from hiddifypanel.models import Child, Role
from hiddifypanel.auth import login_required

from .schema import ChildStatusInputSchema, ChildStatusOutputSchema


class StatusApi(MethodView):
    decorators = [login_required(node_auth=True)]

    @app.input(ChildStatusInputSchema, arg_name='data')  # type: ignore
    @app.output(ChildStatusOutputSchema)  # type: ignore
    def post(self, data):
        logger.info(f"Checking the existence of child with unique_id: {data['child_unique_id']}")
        res = ChildStatusOutputSchema()
        res.existance = False  # type: ignore

        child = Child.query.filter(Child.unique_id == data['child_unique_id']).first()
        if child:
            logger.info(f"Child with unique_id: {data['child_unique_id']} exists")
            res.existance = True  # type: ignore

        return res
