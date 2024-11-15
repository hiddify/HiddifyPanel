import asyncio
import time
from flask import current_app as app, request
from flask import g
from flask.views import MethodView
from apiflask.fields import Dict
from apiflask import Schema
from hiddifypanel.models.usage import DailyUsage
from hiddifypanel.auth import login_required
from hiddifypanel.models import Role, DailyUsage
from hiddifypanel.panel import hiddify, usage
from hiddifypanel import hutils
import json


class UpdateUserUsageApi(MethodView):
    decorators = [login_required({Role.super_admin})]

    def get(self):
        """System: Update User Usage"""
        # time.sleep(5)
        
        return json.dumps(usage.update_local_usage_not_lock(), indent=2)


class AllConfigsApi(MethodView):
    decorators = [login_required({Role.super_admin})]

    def get(self):
        """System: All Configs for configuration"""
        return json.dumps(hiddify.all_configs_for_cli(), indent=2)
