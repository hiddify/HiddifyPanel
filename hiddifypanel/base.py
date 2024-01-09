import flask_bootstrap
import hiddifypanel
from flask import request, g
from flask_babelex import Babel
from flask_session import Session

import datetime

from dotenv import dotenv_values
import os
from hiddifypanel.panel import hiddify
from apiflask import APIFlask
from werkzeug.middleware.proxy_fix import ProxyFix
from hiddifypanel.models import *
from hiddifypanel.panel.init_db import init_db
from hiddifypanel.cache import redis_client


def create_app(cli=False, **config):

    app = APIFlask(__name__, static_url_path="/<proxy_path>/static/", instance_relative_config=True, version='2.0.0', title="Hiddify API",
                   openapi_blueprint_url_prefix="/<proxy_path>/api", docs_ui='elements', json_errors=False, enable_openapi=True)
    # app = Flask(__name__, static_url_path="/<proxy_path>/static/", instance_relative_config=True)
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )
    app.servers = {
        'name': 'current',
        'url': '',
    }  # type: ignore
    app.info = {
        'description': 'Hiddify is a free and open source software. It is as it is.',
        'termsOfService': 'http://hiddify.com',
        'contact': {
            'name': 'API Support',
            'url': 'http://www.hiddify.com/support',
            'email': 'panel@hiddify.com'
        },
        'license': {
            'name': 'Creative Commons Zero v1.0 Universal',
            'url': 'https://github.com/hiddify/Hiddify-Manager/blob/main/LICENSE'
        }
    }

    for c, v in dotenv_values(os.environ.get("HIDDIFY_CFG_PATH", 'app.cfg')).items():
        if v.isdecimal():
            v = int(v)
        else:
            v = True if v.lower() == "true" else (False if v.lower() == "false" else v)

        app.config[c] = v

    # setup flask server-side session
    # app.config['APPLICATION_ROOT'] = './'
    # app.config['SESSION_COOKIE_DOMAIN'] = '/'
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_REDIS'] = redis_client
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=2)
    Session(app)

    app.jinja_env.line_statement_prefix = '%'
    app.jinja_env.filters['b64encode'] = hiddify.do_base_64
    app.view_functions['admin.static'] = {}  # fix bug in apiflask
    app.is_cli = cli
    flask_bootstrap.Bootstrap4(app)

    hiddifypanel.panel.database.init_app(app)
    with app.app_context():
        init_db()

    hiddifypanel.panel.common.init_app(app)
    hiddifypanel.panel.common_bp.init_app(app)
    hiddifypanel.panel.auth.init_app(app)
    hiddifypanel.panel.admin.init_app(app)
    hiddifypanel.panel.user.init_app(app)
    hiddifypanel.panel.commercial.init_app(app)
    hiddifypanel.panel.cli.init_app(app)

    app.config.update(config)  # Override with passed config
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False

    # app.config['BABEL_TRANSLATION_DIRECTORIES'] = '/workspace/Hiddify-Server/hiddify-panel/src/translations.i18n'
    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        # Put your logic here. Application can store locale in
        # user profile, cookie, session, etc.
        from hiddifypanel.models import ConfigEnum, hconfig
        if "admin" in request.base_url:
            g.locale = hconfig(ConfigEnum.admin_lang) or hconfig(ConfigEnum.lang) or 'fa'
        else:
            g.locale = hconfig(ConfigEnum.lang) or "fa"
        return g.locale

    from flask_wtf.csrf import CSRFProtect

    csrf = CSRFProtect(app)

    @app.before_request
    def check_csrf():
        if "/admin/user/" in request.base_url:
            return
        if "/admin/domain/" in request.base_url:
            return
        if "/admin/actions/" in request.base_url:
            return
        if "/api/" in request.base_url:
            return
        csrf.protect()

    @app.after_request
    def apply_no_robot(response):
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
        if response.status_code == 401:
            response.headers['WWW-Authenticate'] = 'Basic realm="Hiddify"'
        return response

    app.jinja_env.globals['get_locale'] = get_locale
    app.jinja_env.globals['version'] = hiddifypanel.__version__
    app.jinja_env.globals['static_url_for'] = hiddify.static_url_for

    return app


def create_app_wsgi():
    # workaround for Flask issue
    # that doesn't allow **config
    # to be passed to create_app
    # https://github.com/pallets/flask/issues/4170
    app = create_app()
    return app


# def create_cli_app():
#     # workaround for Flask issue
#     # that doesn't allow **config
#     # to be passed to create_app
#     # https://github.com/pallets/flask/issues/4170
#     app = create_app(cli=True)
#     return app
