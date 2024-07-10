from apiflask import APIBlueprint

bp = APIBlueprint("api_child", __name__, url_prefix="/<proxy_path>/api/v2/child/", enable_openapi=False)


def init_app(app):
    with app.app_context():
        from .register_parent_api import RegisterWithParentApi
        from .sync_parent_api import SyncWithParentApi
        from .actions import ApplyConfig, Restart, Status, UpdateUsage, Install
        bp.add_url_rule('/sync-parent/', view_func=SyncWithParentApi)
        bp.add_url_rule('/register-parent/', view_func=RegisterWithParentApi)
        bp.add_url_rule('/status/', view_func=Status)
        bp.add_url_rule('/restart/', view_func=Restart)
        bp.add_url_rule('/apply-config/', view_func=ApplyConfig)
        bp.add_url_rule('/install/', view_func=Install)
        bp.add_url_rule('/update-usage/', view_func=UpdateUsage)
    app.register_blueprint(bp)
