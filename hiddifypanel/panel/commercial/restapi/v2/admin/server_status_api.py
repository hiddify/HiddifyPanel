from flask import current_app as app, request
from flask import g
from flask.views import MethodView
from apiflask.fields import Dict
from apiflask import Schema
from hiddifypanel.panel import hiddify
from hiddifypanel.models import get_daily_usage_stats

class ServerStatus(Schema):
    stats = Dict()
    usage_history = Dict()


class AdminServerStatusApi(MethodView):
    decorators = [hiddify.super_admin]

    @app.output(ServerStatus)
    def get(self):
        dto = ServerStatus()
        dto.stats = {
            'system': hiddify.system_stats(),
            'top5': hiddify.top_processes()
        }
        admin_id = request.args.get("admin_id") or g.admin.id
        dto.usage_history = get_daily_usage_stats(admin_id)
        return dto