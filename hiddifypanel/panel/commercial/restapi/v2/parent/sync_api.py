
from flask.views import MethodView
from flask import current_app as app
from flask import g
from apiflask import abort

from hiddifypanel.models.user import User
from hiddifypanel.database import db
from hiddifypanel.models.child import Child
from loguru import logger
from hiddifypanel.models import *
from hiddifypanel.auth import login_required
from .schema import SyncInputSchema, SyncOutputSchema


class SyncApi(MethodView):
    decorators = [login_required(node_auth=True)]

    @app.input(SyncInputSchema, arg_name='data')  # type: ignore
    @app.output(SyncOutputSchema)  # type: ignore
    def put(self, data):
        from hiddifypanel import hutils
        unique_id = Child.node.unique_id

        logger.info(f"Sync child with unique_id: {unique_id}")
        if not hutils.node.is_parent():
            logger.error("Not a parent")
            abort(400, "Not a parent")

        child = Child.query.filter(Child.unique_id == unique_id).first()
        if not child:
            logger.error("The child does not exist")
            abort(404, "The child does not exist")

        try:
            logger.info("Syncing domains...")
            bulk_register_domains(data['domains'], commit=False, force_child_unique_id=child.unique_id)
            logger.info("Syncing hconfigs...")
            bulk_register_configs(data['hconfigs'], commit=False, froce_child_unique_id=child.unique_id)
            logger.info("Syncing proxies...")
            Proxy.bulk_register(data['proxies'], commit=False, force_child_unique_id=child.unique_id)
            db.session.commit()  # type: ignore
        except Exception as err:
            with logger.contextualize(error=err):
                logger.error(f"Error while syncing data")
            abort(400, str(err))

        res = SyncOutputSchema()
        res.users = [u.to_schema() for u in User.query.all()]  # type: ignore
        res.admin_users = [a.to_schema() for a in AdminUser.query.all()]  # type: ignore

        logger.info("Returning sync output")
        return res
