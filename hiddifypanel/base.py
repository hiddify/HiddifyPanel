from dynaconf import FlaskDynaconf
from flask import Flask
from flask_bootstrap import Bootstrap5, SwitchField
from flask_babelex import Babel
from hiddifypanel.panel.database import db
# from flask_babel import Babel


# from werkzeug.middleware.proxy_fix import ProxyFix

def create_app(**config):
    app = Flask(__name__,static_url_path="/<proxy_path>/static/",instance_relative_config=True)
    FlaskDynaconf(app)  # config managed by Dynaconf
    app.jinja_env.line_statement_prefix = '%'
    app.config.load_extensions(
        "EXTENSIONS"
    )  # Load extensions from settings.toml
    app.config.update(config)  # Override with passed config

    babel = Babel(app)
    @babel.localeselector
    def get_locale():
        # Put your logic here. Application can store locale in
        # user profile, cookie, session, etc.
        from hiddifypanel.models import ConfigEnum,hconfig
        return hconfig(ConfigEnum.lang) or "fa"

    from flask_wtf.csrf import CSRFProtect

    csrf = CSRFProtect(app)
    # app=ProxyFix(app, x_for=1, x_host=1,x_proto=1,x_port=1,x_prefix=1)
    app.jinja_env.globals['get_locale'] = get_locale
    

    return app


def create_app_wsgi():
    # workaround for Flask issue
    # that doesn't allow **config
    # to be passed to create_app
    # https://github.com/pallets/flask/issues/4170
    app = create_app()
    return app
