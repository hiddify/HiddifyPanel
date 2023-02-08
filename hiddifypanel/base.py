from dynaconf import FlaskDynaconf
from wtforms.validators import ValidationError
from flask import Flask,request,render_template

import flask_bootstrap 
from flask_babelex import Babel
from hiddifypanel.panel.database import db
from hiddifypanel.models import hconfig,ConfigEnum
# from flask_babel import Babel
import hiddifypanel

from flask import url_for

# from werkzeug.middleware.proxy_fix import ProxyFix

def create_app(**config):
    app = Flask(__name__,static_url_path="/<proxy_path>/static/",instance_relative_config=True)
    FlaskDynaconf(app)  # config managed by Dynaconf
    app.jinja_env.line_statement_prefix = '%'
    flask_bootstrap.Bootstrap4(app)
    hiddifypanel.panel.database.init_app(app)
    hiddifypanel.panel.common.init_app(app)
    hiddifypanel.panel.admin.init_app(app)
    hiddifypanel.panel.user.init_app(app)
    hiddifypanel.panel.cli.init_app(app)
    hiddifypanel.panel.restapi.init_app(app)
    # app.config.load_extensions(
    #     ["flask_bootstrap:Bootstrap4",
    # "hiddifypanel.panel.database:init_app",
    # "hiddifypanel.panel.user:init_app",
    # "hiddifypanel.panel.admin:init_app",
    # "hiddifypanel.panel.cli:init_app",
    # "hiddifypanel.panel.webui:init_app",
    # "hiddifypanel.panel.restapi:init_app",]
    # )  # Load extensions from settings.toml
    app.config.update(config)  # Override with passed config
    app.config['WTF_CSRF_CHECK_DEFAULT']=False
    
    
    babel = Babel(app)
    @babel.localeselector
    def get_locale():
        # Put your logic here. Application can store locale in
        # user profile, cookie, session, etc.
        from hiddifypanel.models import ConfigEnum,hconfig
        if "admin" in request.base_url:
            return hconfig(ConfigEnum.admin_lang) or hconfig(ConfigEnum.lang) or 'fa'
        return hconfig(ConfigEnum.lang) or "fa"

    from flask_wtf.csrf import CSRFProtect

    csrf = CSRFProtect(app)
    @app.before_request
    def check_csrf():
        if  "/admin/user/" in request.base_url :return
        if  "/admin/domain/" in request.base_url :return
        if "/admin/actions/" in request.base_url :return
        csrf.protect()
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
