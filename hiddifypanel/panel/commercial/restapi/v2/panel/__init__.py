from apiflask import APIBlueprint

bp = APIBlueprint("api_panel", __name__, url_prefix="/<proxy_path>/api/v2/panel/", enable_openapi=True)


def init_app(app):

    with app.app_context():
        from .info import PanelInfoApi
        from .ping_pong import PingPongApi
        bp.add_url_rule('/info/', view_func=PanelInfoApi)
        bp.add_url_rule('/ping/', view_func=PingPongApi)
    app.register_blueprint(bp)
