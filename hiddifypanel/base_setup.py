from flask import request, g
import redis
# from hiddifypanel.cache import cache
from hiddifypanel.models import *

import flask_bootstrap
from flask_babel import Babel
from flask_session import Session

import datetime

from dotenv import dotenv_values
import os
import sys
from werkzeug.middleware.proxy_fix import ProxyFix
from loguru import logger
from sonora.wsgi import grpcWSGI



def init_app(app):
        from hiddifypanel import auth
        app.config["PREFERRED_URL_SCHEME"] = "https"
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1,
        )
        

        app.secret_key="asdsad"
        app.servers = {
            'name': 'current',
            'url': '',
        }  # type: ignore
        app.info = {
            'description': 'Hiddify is a free and open source software. It is as it is.',
            'termsOfService': 'https://hiddify.com',
            'contact': {
                'name': 'API Support',
                'url': 'https://www.hiddify.com/support',
                'email': 'panel@hiddify.com'
            },
            'license': {
                'name': 'Creative Commons Zero v1.0 Universal',
                'url': 'https://github.com/hiddify/Hiddify-Manager/blob/main/LICENSE'
            }
        }
        # setup flask server-side session
        # app.config['APPLICATION_ROOT'] = './'
        # app.config['SESSION_COOKIE_DOMAIN'] = '/'
        

        app.jinja_env.line_statement_prefix = '%'
        from hiddifypanel import hutils
        app.jinja_env.filters['b64encode'] = hutils.encode.do_base_64
        app.view_functions['admin.static'] = {}  # fix bug in apiflask
        flask_bootstrap.Bootstrap4(app)

        def get_locale():
            # Put your logic here. Application can store locale in
            # user profile, cookie, session, etc.
            if "admin" in request.base_url:
                g.locale = hconfig(ConfigEnum.admin_lang) or 'en'
            else:
                g.locale = auth.current_account.lang or hconfig(ConfigEnum.lang) or 'en'
            return g.locale
        app.jinja_env.globals['get_locale'] = get_locale
        babel = Babel(app, locale_selector=get_locale)
        
        app.config['SESSION_TYPE'] = 'redis'
        
        app.config['SESSION_REDIS'] = redis.from_url(os.environ['REDIS_URI_MAIN'])
        app.config['SESSION_PERMANENT'] = True
        app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=10)
        app.security_schemes = {  # equals to use config SECURITY_SCHEMES
            'Hiddify-API-Key': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Hiddify-API-Key',
            }
        }
        Session(app)
        app.wsgi_app = grpcWSGI(app.wsgi_app)