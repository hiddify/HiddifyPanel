from .login import LoginView
from apiflask import APIBlueprint
bp = APIBlueprint("common_bp", __name__, url_prefix="/<proxy_path>/", template_folder="templates", enable_openapi=False)


def init_app(app):
    LoginView.register(bp, route_base="/")
    app.register_blueprint(bp)
