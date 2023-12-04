
from urllib.parse import urlparse
from apiflask import Schema
from flask import g, request
from apiflask.fields import String,Integer
from flask import current_app as app
from datetime import datetime
from flask.views import MethodView
from hiddifypanel.models.config import hconfig
from hiddifypanel.models.config_enum import ConfigEnum
from hiddifypanel.panel import hiddify

class ShortSchema(Schema):
    short = String(required=True, description="the short url slug")
    full_url = String(required=True, description="full short url")
    expire_in = Integer(required=True, description="expire_in is in seconds")
class ShortAPI(MethodView):
    decorators = [hiddify.user_auth]

    @app.output(ShortSchema)
    def get(self):
        short, expire_date = hiddify.add_short_link("/"+hconfig(ConfigEnum.proxy_path)+"/"+str(g.user_uuid)+"/")
        full_url = f"https://{urlparse(request.base_url).hostname}/{short}"
        dto = ShortSchema()
        dto.full_url = full_url
        dto.short = short
        # expire_in is in seconds
        dto.expire_in = (expire_date - datetime.now()).seconds
        return dto