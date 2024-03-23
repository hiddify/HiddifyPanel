from apiflask import APIBlueprint

bp = APIBlueprint("api_child", __name__, url_prefix="/<proxy_path>/api/v2/child/", enable_openapi=True)


def init_app(app):
    with app.app_context():
        from .register_parent import RegisterParent
        bp.add_url_rule('/register-parent/', view_func=RegisterParent)
    app.register_blueprint(bp)
