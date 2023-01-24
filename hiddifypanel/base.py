from dynaconf import FlaskDynaconf
from flask import Flask
from flask_bootstrap import Bootstrap5, SwitchField


# from werkzeug.middleware.proxy_fix import ProxyFix

def create_app(**config):
    app = Flask(__name__,static_url_path="/<proxy_path>/static/")
    FlaskDynaconf(app)  # config managed by Dynaconf
    app.jinja_env.line_statement_prefix = '%'
    app.config.load_extensions(
        "EXTENSIONS"
    )  # Load extensions from settings.toml
    app.config.update(config)  # Override with passed config


    # app=ProxyFix(app, x_for=1, x_host=1,x_proto=1,x_port=1,x_prefix=1)
    return app


def create_app_wsgi():
    # workaround for Flask issue
    # that doesn't allow **config
    # to be passed to create_app
    # https://github.com/pallets/flask/issues/4170
    app = create_app()
    return app
