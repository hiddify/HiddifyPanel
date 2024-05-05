from apiflask import abort
from hiddifypanel.database import db
from flask import current_app as app
from flask.views import MethodView
from loguru import logger

from hiddifypanel.models import *
from hiddifypanel.auth import login_required

from .schema import RegisterInputSchema, RegisterOutputSchema


class RegisterApi(MethodView):
    decorators = [login_required({Role.super_admin})]

    @app.input(RegisterInputSchema, arg_name='data')  # type: ignore
    @app.output(RegisterOutputSchema)  # type: ignore
    def put(self, data):
        from hiddifypanel import hutils
        logger.info("Register child panel with unique_id: {}", data['unique_id'])
        if hutils.node.is_child():
            logger.error("The panel in child, not a parent nor standalone")
            abort(400, 'The panel in child, not a parent nor standalone')

        unique_id = data['unique_id']
        name = data['name']
        mode = data['mode']

        child = Child.query.filter(Child.unique_id == unique_id).first()
        if not child:
            logger.info("Adding new child with unique_id: {}", unique_id)
            child = Child(unique_id=unique_id, name=name, mode=mode)
            db.session.add(child)  # type: ignore
            db.session.commit()  # type: ignore
            child = Child.query.filter(Child.unique_id == unique_id).first()

        try:
            # add data
            logger.info("Adding admin users...")
            AdminUser.bulk_register(data['panel_data']['admin_users'], commit=False)
            logger.info("Adding users...")
            User.bulk_register(data['panel_data']['users'], commit=False)
            logger.info("Adding domains...")
            Domain.bulk_register(data['panel_data']['domains'], commit=False, force_child_unique_id=child.unique_id)
            logger.info("Adding hconfigs...")
            bulk_register_configs(data['panel_data']['hconfigs'], commit=False, froce_child_unique_id=child.unique_id)
            logger.info("Adding proxies...")
            Proxy.bulk_register(data['panel_data']['proxies'], commit=False, force_child_unique_id=child.unique_id)
            db.session.commit()  # type: ignore
        except Exception as err:
            with logger.contextualize(error=err):
                logger.error("Error while registering data")
            abort(400, str(err))

        if not hutils.node.is_parent():
            logger.info("Setting panel to parent mode")
            set_hconfig(ConfigEnum.panel_mode, PanelMode.parent)  # type: ignore

        logger.info("Returning register output")
        res = RegisterOutputSchema()
        res.users = [u.to_schema() for u in User.query.all()]  # type: ignore
        res.admin_users = [a.to_schema() for a in AdminUser.query.all()]  # type: ignore
        res.parent_unique_id = hconfig(ConfigEnum.unique_id)

        return res
