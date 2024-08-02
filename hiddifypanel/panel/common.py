import traceback
from flask import render_template, request, jsonify
from flask import g, send_from_directory, session
from flask_babel import gettext as _
import hiddifypanel
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
from hiddifypanel import hutils
import hiddifypanel.auth as auth
from hiddifypanel.auth import current_account
from apiflask import APIFlask, HTTPError, abort
from hiddifypanel import hutils
from loguru import logger


def init_app(app: APIFlask):
    app.jinja_env.globals['ConfigEnum'] = ConfigEnum
    app.jinja_env.globals['DomainType'] = DomainType
    app.jinja_env.globals['UserMode'] = UserMode
    app.jinja_env.globals['hconfig'] = hconfig
    app.jinja_env.globals['g'] = g
    app.jinja_env.globals['hutils'] = hutils
    app.jinja_env.globals['hiddify'] = hiddify
    app.jinja_env.globals['version'] = hiddifypanel.__version__
    app.jinja_env.globals['static_url_for'] = hutils.flask.static_url_for
    app.jinja_env.globals['hurl_for'] = hutils.flask.hurl_for
    app.jinja_env.globals['_gettext'] = lambda x: print("==========", x)
    app.jinja_env.globals['proxy_stats_url'] = hutils.flask.get_proxy_stats_url

    @app.after_request
    def apply_no_robot(response):
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
        response.headers["Referrer-Policy"] = "same-origin"
        if response.status_code == 401:
            response.headers['WWW-Authenticate'] = 'Basic realm="Hiddify"'
        return response

    @app.errorhandler(Exception)
    def internal_server_error(e):
        logger.exception(e)
        if isinstance(e, Exception):
            if hutils.flask.is_api_call(request.path):
                return {
                    'msg': str(e),
                }, 500

        if hasattr(e, 'code') and e.code == 404:
            return jsonify({
                'message': 'Not Found',
            }), 404

        has_update = hutils.utils.is_panel_outdated()

        if not request.accept_mimetypes.accept_html:
            if has_update:
                return jsonify({
                    'message': 'This version of Hiddify Panel is outdated. please update it from admin area.',
                }), 500

            return jsonify({'message': str(e),
                            'detail': [f'{filename}:{line} {function}: {text}' for filename, line, function, text in traceback.extract_tb(e.__traceback__)],
                            'version': hiddifypanel.__version__,
                            }), 500

        trace = traceback.format_exc()

        # Create github issue link
        issue_link = hutils.github_issue.generate_github_issue_link_for_500_error(e, trace)
        last_version = hiddify.get_latest_release_version('hiddifypanel')

        return render_template('500.html', error=e, trace=trace, has_update=has_update, last_version=last_version, issue_link=issue_link), 500

    @app.errorhandler(HTTPError)
    def internal_server_error(e):
        # print(request.headers)
        if not request.accept_mimetypes.accept_html:
            return app.error_callback(e)
        # if it's interval server error
        if e.status_code == 500:
            trace = traceback.format_exc()

            # Create github issue link
            issue_link = hutils.github_issue.generate_github_issue_link_for_500_error(e, trace)

            has_update = hutils.utils.is_panel_outdated()
            last_version = hiddify.get_latest_release_version('hiddifypanel')

            return render_template('500.html', error=e, trace=trace, has_update=has_update, last_version=last_version, issue_link=issue_link), 500

        # if it's access denied error
        # if e.status_code in [400,401,403]:
        #     return render_template('access-denied.html',error=e), e.status_code

        # if it's api error
        if hutils.flask.is_api_call(request.path):
            return {
                'msg': e.message,
            }, e.status_code

        return render_template('error.html', error=e), e.status_code

    @app.url_defaults
    def add_proxy_path_user(endpoint, values):
        if 'static' in endpoint:
            values['proxy_path'] = g.proxy_path
        if 'proxy_path' not in values:
            if force_path := g.get('force_proxy_path'):
                values['proxy_path'] = force_path
            elif hutils.flask.is_admin_role(current_account.role):  # type: ignore
                values['proxy_path'] = hconfig(ConfigEnum.proxy_path_admin)
            elif hutils.flask.is_user_panel_call():
                values['proxy_path'] = hconfig(ConfigEnum.proxy_path_client)
            elif current_account and hutils.flask.is_admin_role(current_account.role):  # type: ignore
                values['proxy_path'] = hconfig(ConfigEnum.proxy_path_admin)
            else:
                values['proxy_path'] = g.proxy_path or "A"
        if "child_id" not in values and g.__child_id != 0:
            values['child_id'] = g.child.id

        if hutils.flask.is_api_v1_call(endpoint=endpoint) and 'admin_uuid' not in values:
            values['admin_uuid'] = AdminUser.get_super_admin_uuid()

        # if 'secret_uuid' not in values and g.account and ".webmanifest" in request.path:
        #     values['secret_uuid'] = g.account.uuid

    @app.route("/<proxy_path>/videos/<file>")
    @app.doc(hide=True)
    def videos(file):
        print("file", file, app.config['HIDDIFY_CONFIG_PATH'] +
              '/hiddify-panel/videos/' + file)
        return send_from_directory(app.config['HIDDIFY_CONFIG_PATH'] + '/hiddify-panel/videos/', file)

    @app.url_value_preprocessor
    def pull_default(endpoint, values):
        g.__child_id = 0
        g.uuid = None
        g.proxy_path = None
        g.user_agent = hutils.flask.get_user_agent()

        if values:
            g.proxy_path = values.pop('proxy_path', None)
            if 'secret_uuid' in values:
                g.uuid = values.pop('secret_uuid', None)

            g.__child_id = values.pop('child_id', 0)
        g.child = Child.by_id(g.__child_id) or abort(404, "Child not found")
        g.account = current_account

    @app.before_request
    def base_middleware():
        if "generate_204" in request.path:
            return "", 204
        if request.endpoint == 'static' or request.endpoint == "videos":
            return

        if g.user_agent['is_bot']:
            abort(400, "invalid")

        g.proxy_path = hutils.flask.get_proxy_path_from_url(request.url)
        hutils.flask.proxy_path_validator(g.proxy_path)

        # setup dark mode
        if request.args.get('darkmode') is not None:
            session['darkmode'] = request.args.get('darkmode', '').lower() == 'true'
        g.darkmode = session.get('darkmode', False)

        # setup pwa
        import random
        g.install_pwa = random.random() <= 0.05
        if request.args.get('pwa') is not None:
            session['pwa'] = request.args.get('pwa', '').lower() == 'true'
        g.pwa = session.get('pwa', False)

        # setup telegram bot
        if hconfig(ConfigEnum.telegram_bot_token):
            import hiddifypanel.panel.commercial.telegrambot as telegrambot
            g.bot = telegrambot.bot
        else:
            g.bot = None

        if auth_before := auth.auth_before_request():
            return auth_before

    app.jinja_env.globals['generate_github_issue_link_for_admin_sidebar'] = hutils.github_issue.generate_github_issue_link_for_admin_sidebar
    with app.app_context():
        import hiddifypanel.panel.commercial.telegrambot as telegrambot
        if (not telegrambot.bot) or (not telegrambot.bot.username):  # type: ignore
            telegrambot.register_bot_cached(set_hook=True)
