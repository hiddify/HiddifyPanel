from apiflask import fields, Schema
from flask import current_app as app
from flask import g
from flask.views import MethodView
from loguru import logger

from hiddifypanel.models.child import Child
from hiddifypanel.panel.run_commander import commander, Command
from hiddifypanel.auth import login_required


class Status(MethodView):
    decorators = [login_required(node_auth=True)]

    def post(self):
        logger.info(f"Status action called by parent: {Child.node.unique_id}")
        commander(Command.status)
        return {'status': 200, 'msg': 'ok'}


class UpdateUsage(MethodView):
    decorators = [login_required(node_auth=True)]

    def post(self):
        logger.info(f"Update usage action called by parent: {Child.node.unique_id}")
        commander(Command.update_usage)
        return {'status': 200, 'msg': 'ok'}


class Restart(MethodView):
    decorators = [login_required(node_auth=True)]

    def post(self):
        logger.info(f"Restart action called by parent: {Child.node.unique_id}")
        commander(Command.restart_services)
        return {'status': 200, 'msg': 'ok'}


class ApplyConfig(MethodView):
    decorators = [login_required(node_auth=True)]

    def post(self):
        logger.info(f"Apply config action called by parent: {Child.node.unique_id}")
        commander(Command.apply)
        return {'status': 200, 'msg': 'ok'}


class InstallSchema(Schema):
    full = fields.Boolean(description="full install", required=True, default=True)


class Install(MethodView):
    decorators = [login_required(node_auth=True)]

    @app.input(InstallSchema, arg_name="data")  # type: ignore
    def post(self, data: dict):
        if data.get('full'):
            logger.info(f"Install action called by parent: {Child.node.unique_id}, full=True")
            commander(Command.install)
        else:
            logger.info(f"Install action called by parent: {Child.node.unique_id}, full=False")
            commander(Command.apply)
        return {'status': 200, 'msg': 'ok'}
