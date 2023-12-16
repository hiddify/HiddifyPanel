from flask import current_app as app, request
from flask import g
from flask.views import MethodView
from apiflask.fields import Dict
from apiflask import Schema
from hiddifypanel.panel import hiddify
from hiddifypanel.models import get_daily_usage_stats
from hiddifypanel.panel.authentication import api_auth


class ServerStatus(Schema):
    stats = Dict(required=True, description="System stats")
    usage_history = Dict(required=True, description="System usage history")


class AdminServerStatusApi(MethodView):
    decorators = [hiddify.admin]

    @app.output(ServerStatus)
    def get(self):
        dto = ServerStatus()
        dto.stats = {
            'system': hiddify.system_stats(),
            'top5': hiddify.top_processes()
        }
        admin_id = request.args.get("admin_id") or g.account.id
        dto.usage_history = get_daily_usage_stats(admin_id)
        return dto
