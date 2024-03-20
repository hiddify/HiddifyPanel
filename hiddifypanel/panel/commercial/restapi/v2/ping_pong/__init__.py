from apiflask import APIBlueprint

bp = APIBlueprint("api_ping", __name__, url_prefix="/<proxy_path>/api/v2/ping/", enable_openapi=True)


def init_app(app):

    with app.app_context():
        from .ping_pong import Ping_Pong
        bp.add_url_rule('/', view_func=Ping_Pong)
    app.register_blueprint(bp)
