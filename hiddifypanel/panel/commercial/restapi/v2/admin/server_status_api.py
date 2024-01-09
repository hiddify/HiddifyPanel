from flask import current_app as app, request
from flask import g
from flask.views import MethodView
from apiflask.fields import Dict
from apiflask import Schema
from hiddifypanel.models.usage import DailyUsage
from hiddifypanel.panel.auth import login_required
from hiddifypanel.models import Role, DailyUsage
from hiddifypanel.panel import hiddify


class ServerStatus(Schema):
    stats = Dict(required=True, description="System stats")
    usage_history = Dict(required=True, description="System usage history")


class AdminServerStatusApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin, Role.agent})]

    @app.output(ServerStatus)  # type: ignore
    def get(self):
        dto = ServerStatus()
        dto.stats = {  # type: ignore
            'system': hiddify.system_stats(),
            'top5': hiddify.top_processes()
        }
        admin_id = request.args.get("admin_id") or g.account.id
        dto.usage_history = DailyUsage.get_daily_usage_stats(admin_id)  # type: ignore
        return dto
