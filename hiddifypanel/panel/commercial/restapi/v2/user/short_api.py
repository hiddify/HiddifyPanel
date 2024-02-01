
from urllib.parse import urlparse
from apiflask import Schema
from flask import g, request
from apiflask.fields import String, Integer
from flask import current_app as app
from flask.views import MethodView
from hiddifypanel.auth import login_required
from hiddifypanel.models.config import hconfig
from hiddifypanel.models.config_enum import ConfigEnum
from hiddifypanel.models.role import Role
from hiddifypanel.panel import hiddify


class ShortSchema(Schema):
    short = String(required=True, description="the short url slug")
    full_url = String(required=True, description="full short url")
    expire_in = Integer(required=True, description="expire_in is in seconds")


class ShortAPI(MethodView):
    decorators = [login_required({Role.user})]

    @app.output(ShortSchema)
    def get(self):
        short, expire_in = hiddify.add_short_link(hiddify.get_account_panel_link(g.account, request.host))
        full_url = f"https://{request.host}/{short}"
        dto = ShortSchema()
        dto.full_url = full_url
        dto.short = short
        # expire_in is in seconds
        dto.expire_in = expire_in
        return dto
