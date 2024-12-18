from flask import request, g
# from hiddifypanel.cache import cache



import datetime

from dotenv import dotenv_values
import os
import sys
from apiflask import APIFlask
from loguru import logger


from dynaconf import FlaskDynaconf

def create_app(*args, app_mode="web", **config):
    
    app = APIFlask(__name__, static_url_path="/<proxy_path>/static/", instance_relative_config=True, version='2.2.0', title="Hiddify API",
                   openapi_blueprint_url_prefix="/<proxy_path>/api", docs_ui='elements', json_errors=False, enable_openapi=app_mode=="web")
    # app = Flask(__name__, static_url_path="/<proxy_path>/static/", instance_relative_config=True)
    # app.asgi_app = WsgiToAsgi(app)
    
    for c, v in dotenv_values(os.environ.get("HIDDIFY_CFG_PATH", 'app.cfg')).items():
        if v.isdecimal():
            v = int(v)
        else:
            v = True if v.lower() == "true" else (False if v.lower() == "false" else v)
        app.config[c] = v
    dyn=FlaskDynaconf(app,settings_files=[os.environ.get("HIDDIFY_CFG_PATH", 'app.cfg')])
    
    extensions=[
        # "hiddifypanel.cache:init_app",
        "hiddifypanel.database:init_app",
        "hiddifypanel.panel.hlogger:init_cli",
    ]
    
    if app_mode=="celery":
        extensions.append("hiddifypanel.celery:init_app")
    elif app_mode=="cli":
        extensions.append("hiddifypanel.panel.cli:init_app")
    else:
        extensions.extend([
            "hiddifypanel.base_setup:init_app",
            "hiddifypanel.panel.common:init_app",
            "hiddifypanel.panel.common_bp:init_app",
            "hiddifypanel.panel.admin:init_app",
            "hiddifypanel.panel.user:init_app",
            "hiddifypanel.panel.commercial:init_app",
            "hiddifypanel.panel.node:init_app",
            "hiddifypanel.celery:init_app",
        ])
    
    app.config['EXTENSIONS']=extensions

    app.config.update(config)  # Override with passed config
    
    app.config.load_extensions("EXTENSIONS")
    return app


def create_app_wsgi(*args, **kwargs):
    # workaround for Flask issue
    # that doesn't allow **config
    # to be passed to create_app
    # https://github.com/pallets/flask/issues/4170
    cli = ("hiddifypanel" in sys.argv[0] ) or (sys.argv[1] in ["update-usage", "all-configs", "admin_links", "admin_path"])

    app = create_app(app_mode="cli" if cli else "web")
    return app



def create_celery_app():
    #     # workaround for Flask issue
    #     # that doesn't allow **config
    #     # to be passed to create_app
    #     # https://github.com/pallets/flask/issues/4170
    # print(kwargs)
    app = create_app(app_mode="celery")
    return app.extensions["celery"]
