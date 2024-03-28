
from flask.views import MethodView
from flask import current_app as app
from flask import g
from apiflask import abort

from hiddifypanel.models.user import User
from hiddifypanel.database import db
from hiddifypanel.models.child import Child
from hiddifypanel.models import *
from hiddifypanel.auth import login_required
from .schema import SyncInputSchema, SyncOutputSchema


class SyncApi(MethodView):
    decorators = [login_required(node_auth=True)]

    @app.input(SyncInputSchema, arg_name='data')  # type: ignore
    @app.output(SyncOutputSchema)  # type: ignore
    def put(self, data):
        from hiddifypanel import hutils
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
