from apiflask import APIBlueprint
from marshmallow import ValidationError
from hiddifypanel.models import ConfigEnum

bp = APIBlueprint("api_parent", __name__, url_prefix="/<proxy_path>/<user_secret>/api/v2/parent/", enable_openapi=True)


def init_app(app):
    with app.app_context():
        from .register_api import RegisterApi
        from .sync_api import SyncApi
        from .usage_api import UsageApi
        bp.add_url_rule('/register/', view_func=RegisterApi)
        bp.add_url_rule('/sync/', view_func=SyncApi)
        bp.add_url_rule('/usage/', view_func=UsageApi)
    app.register_blueprint(bp)


def hconfig_key_validator(value):
    if value not in [c.name for c in ConfigEnum]:
        raise ValidationError(f"{value} is not a valid hconfig key.")
    return value
