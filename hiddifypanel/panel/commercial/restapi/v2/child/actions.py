from apiflask import abort, fields, Schema
from flask import current_app as app
from flask.views import MethodView

from hiddifypanel.panel.run_commander import commander, Command
from hiddifypanel.auth import login_required


class Status(MethodView):
    decorators = [login_required(node_auth=True)]

    def post(self):
        commander(Command.status)
        return {'status': 200, 'msg': 'ok'}


class UpdateUsage(MethodView):
    decorators = [login_required(node_auth=True)]

    def post(self):
        commander(Command.update_usage)
        return {'status': 200, 'msg': 'ok'}


class Restart(MethodView):
    decorators = [login_required(node_auth=True)]

    def post(self):
        commander(Command.restart_services)
        return {'status': 200, 'msg': 'ok'}


class ApplyConfig(MethodView):
    decorators = [login_required(node_auth=True)]

    def post(self):
        commander(Command.apply)
        return {'status': 200, 'msg': 'ok'}


class InstallSchema(Schema):
    full = fields.Boolean(description="full install", required=True, default=True)


class Install(MethodView):
    decorators = [login_required(node_auth=True)]

    @app.input(InstallSchema, arg_name="data")  # type: ignore
    def post(self, data: dict):
        if data.get('full'):
            commander(Command.install)
        else:
            commander(Command.apply)
        return {'status': 200, 'msg': 'ok'}
