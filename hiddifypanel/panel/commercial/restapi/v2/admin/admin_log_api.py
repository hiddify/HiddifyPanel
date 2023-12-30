from apiflask import Schema, fields, abort
from flask.views import MethodView
from hiddifypanel.models.role import Role
from hiddifypanel.panel import hiddify
from flask import current_app as app
from flask_cors import cross_origin
import os
from ansi2html import Ansi2HTMLConverter
from hiddifypanel.panel.auth import login_required


class AdminLogfileSchema(Schema):
    file = fields.String(description="The log file name", required=True)


class AdminLogApi(MethodView):
    decorators = [login_required({Role.super_admin})]

    @app.input(AdminLogfileSchema, arg_name="data", location='form')
    @app.output(fields.String(description="The html of the log"))
    # enable CORS for javascript calls
    @cross_origin(supports_credentials=True)
    def post(self, data):
        file = data.get('file') or abort(400, "Parameter issue: 'file'")
        file_path = f"{app.config['HIDDIFY_CONFIG_PATH']}/log/system/{file}"
        if not os.path.exists(file_path):
            return abort(404, "Invalid log file")
        logs = ''
        with open(file_path, 'r') as f:
            lines = [line for line in f]
            logs = "".join(lines)

        conv = Ansi2HTMLConverter()
        html_log = f'<div style="background-color:black; color:white;padding:10px">{conv.convert(logs)}</div>'

        return html_log
