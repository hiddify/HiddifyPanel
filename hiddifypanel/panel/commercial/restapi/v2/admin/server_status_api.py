from flask import current_app as app, request
from flask import g
from flask.views import MethodView
from apiflask.fields import Dict
from apiflask import Schema
from hiddifypanel.models.usage import DailyUsage
from hiddifypanel.auth import login_required
from hiddifypanel.models import Role, DailyUsage
from hiddifypanel.panel import hiddify
from hiddifypanel import hutils


class ServerStatusOutputSchema(Schema):
    stats = Dict(required=True, description="System stats")
    usage_history = Dict(required=True, description="System usage history")


class AdminServerStatusApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin, Role.agent})]

    @app.output(ServerStatusOutputSchema)  # type: ignore
    def get(self):
        """System: ServerStatus"""
        dto = ServerStatusOutputSchema()
        dto.stats = {  # type: ignore
            'system': hutils.system.system_stats(),
            'top5': hutils.system.top_processes()
        }
        admin_id = request.args.get("admin_id") or g.account.id
        dto.usage_history = DailyUsage.get_daily_usage_stats(admin_id)  # type: ignore
        return dto
