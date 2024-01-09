import traceback
import re
import user_agents
from flask import render_template, request, jsonify, redirect
from flask import g, send_from_directory, session
from flask_babelex import gettext as _
import hiddifypanel
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify, github_issue_generator
from sys import version as python_version
from platform import platform
import hiddifypanel.hutils as hutils
import hiddifypanel.panel.auth as auth
from apiflask import APIFlask, HTTPError, abort


def init_app(app: APIFlask):
    app.jinja_env.globals['ConfigEnum'] = ConfigEnum
    app.jinja_env.globals['DomainType'] = DomainType
    app.jinja_env.globals['UserMode'] = UserMode
    app.jinja_env.globals['hconfig'] = hconfig
    app.jinja_env.globals['g'] = g

    @app.errorhandler(Exception)
    def internal_server_error(e):
        if hasattr(e, 'code') and e.code == 404:
            return jsonify({
                'message': 'Not Found',
            }), 404
        # print(request.headers)
        last_version = hiddify.get_latest_release_version('hiddify-panel')  # TODO: add dev update check
        if "T" in hiddifypanel.__version__:
            has_update = False
        else:
            has_update = "dev" not in hiddifypanel.__version__ and f'{last_version}' != hiddifypanel.__version__

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
        issue_link = generate_github_issue_link_for_500_error(e, trace)

        return render_template('500.html', error=e, trace=trace, has_update=has_update, last_version=last_version, issue_link=issue_link), 500

    @app.errorhandler(HTTPError)
    def internal_server_error(e):
        # print(request.headers)
        if not request.accept_mimetypes.accept_html:
            return app.error_callback(e)
        if e.status_code == 500:
            trace = traceback.format_exc()

            # Create github issue link
            issue_link = generate_github_issue_link_for_500_error(e, trace)

            last_version = hiddify.get_latest_release_version('hiddify-panel')  # TODO: add dev update check
            if "T" in hiddifypanel.__version__:
                has_update = False
            else:
                has_update = "dev" not in hiddifypanel.__version__ and f'{last_version}' != hiddifypanel.__version__

            return render_template('500.html', error=e, trace=trace, has_update=has_update, last_version=last_version, issue_link=issue_link), 500
        # if e.status_code in [400,401,403]:
        #     return render_template('access-denied.html',error=e), e.status_code

        return render_template('error.html', error=e), e.status_code

    def generate_github_issue_link(title, issue_body):
        opts = {
            "user": 'hiddify',
            "repo": 'Hiddify-Manager',
            "title": title,
            "body": issue_body,
        }
        issue_link = str(github_issue_generator.IssueUrl(opts).get_url())
        return issue_link

    # @app.spec_processor
    # def set_default_path_values(spec):
    #     # for path in spec['paths'].values():
    #         # for operation in path.values():
    #             # if 'parameters' in operation:
    #                 # for parameter in operation['parameters']:
    #                 #     if parameter['name'] == 'proxy_path':
    #                 #         parameter['schema'] = {'type': 'string', 'default': g.proxy_path}
    #                 # elif parameter['name'] == 'user_secret':
    #                 #     parameter['schema'] = {'type': 'string', 'default': g.account_uuid}
    #     return spec

    @app.url_defaults
    def add_proxy_path_user(endpoint, values):
        if 'proxy_path' not in values:

            if hasattr(g, 'account') and isinstance(g.account, AdminUser):
                values['proxy_path'] = hconfig(ConfigEnum.proxy_path_admin)
            # elif 'static' in endpoint:
                #     values['proxy_path'] = hconfig(ConfigEnum.proxy_path)
            elif hiddify.is_user_panel_call():
                values['proxy_path'] = hconfig(ConfigEnum.proxy_path_client)
            elif g.account and hiddify.is_admin_role(g.account.role):
                values['proxy_path'] = hconfig(ConfigEnum.proxy_path_admin)
            else:
                values['proxy_path'] = g.proxy_path

        if hiddify.is_api_v1_call(endpoint=endpoint) and 'admin_uuid' not in values:
            values['admin_uuid'] = AdminUser.get_super_admin_uuid()
        # if 'secret_uuid' not in values:
        #     values['secret_uuid'] = AdminUser.get_super_admin_uuid()

    @app.route("/<proxy_path>/videos/<file>")
    @app.doc(hide=True)
    def videos(file):
        print("file", file, app.config['HIDDIFY_CONFIG_PATH'] +
              '/hiddify-panel/videos/'+file)
        return send_from_directory(app.config['HIDDIFY_CONFIG_PATH']+'/hiddify-panel/videos/', file)
    # @app.template_filter()
    # def rel_datetime(value):
    #     diff=datetime.datetime.now()-value
    #     return format_timedelta(diff, add_direction=True, locale=hconfig(ConfigEnum.lang))

    # @app.before_request
    # def backward_compatibility_middleware():
    #     # get needed variables
    #     g.user_agent_old = user_agent = user_agents.parse(request.user_agent.string)

    #     proxy_path = hiddify.get_proxy_path_from_url(request.url)
    #     if not proxy_path:
    #         abort(400, "invalid")

    #     # get proxy paths
    #     deprecated_proxy_path = hconfig(ConfigEnum.proxy_path)
    #     if proxy_path != deprecated_proxy_path:
    #         return

    #     if user_agent.is_bot:
    #         abort(400, "invalid")

    #     uuid = hutils.utils.get_uuid_from_url_path(request.path)
    #     account = User.by_uuid(uuid) or AdminUser.by_uuid(uuid) or abort(400, 'invalid request2')

    #     admin_proxy_path = hconfig(ConfigEnum.proxy_path_admin)
    #     client_proxy_path = hconfig(ConfigEnum.proxy_path_client)

    #     new_link = ''

    #     # handle deprecated proxy path
    #     new_link = f"https://{request.host}"
    #     if hiddify.is_admin_panel_call(deprecated_format=True):
    #         new_link += request.path.replace(f"{proxy_path}/{uuid}/admin/", f'{admin_proxy_path}/admin/')
    #     elif hiddify.is_user_panel_call(deprecated_format=True):
    #         new_link += request.path.replace(f"{proxy_path}/{uuid}/", f'{client_proxy_path}/client/')
    #     else:
    #         return abort(400, 'invalid request 1')

    #     new_link = hutils.utils.add_basic_auth_to_url(new_link, account.username, account.password)

    #     if user_agent.browser:
    #         return render_template('redirect_to_new_format.html', new_link=new_link)

    #     auth.login_user(account)
    #     # return new_link
    #     return redirect(new_link, 302)
    @app.before_request
    def set_default_values():
        g.user_agent = hiddify.get_user_agent()

    @app.before_request
    def base_middleware():
        if request.endpoint == 'static' or request.endpoint == "videos":
            return

        # validate request made by human (just check user agent, there's no capcha)
        # g.user_agent_old = user_agents.parse(request.user_agent.string)
        if g.user_agent['is_bot']:
            abort(400, "invalid")

        # validate proxy path

        # g.proxy_path = hutils.utils.get_proxy_path_from_url(request.url)
        hiddify.proxy_path_validator(g.proxy_path)

        # if g.proxy_path != hconfig(ConfigEnum.proxy_path):
        #     if app.config['DEBUG']:
        #         abort(400, Markup(
        #             f"Invalid Proxy Path <a href=/{hconfig(ConfigEnum.proxy_path)}/admin>admin</a>"))
        #     abort(400, "Invalid Proxy Path")

        # setup dark mode
        if request.args.get('darkmode') != None:
            session['darkmode'] = request.args.get(
                'darkmode', '').lower() == 'true'
        g.darkmode = session.get('darkmode', False)

        # setup pwa
        import random
        g.install_pwa = random.random() <= 0.05
        if request.args.get('pwa') != None:
            session['pwa'] = request.args.get('pwa', '').lower() == 'true'
        g.pwa = session.get('pwa', False)

        # setup telegram bot
        if hconfig(ConfigEnum.telegram_bot_token):
            import hiddifypanel.panel.commercial.telegrambot as telegrambot
            if (not telegrambot.bot) or (not telegrambot.bot.username):  # type: ignore
                telegrambot.register_bot(set_hook=True)
            g.bot = telegrambot.bot
        else:
            g.bot = None

    def github_issue_details():
        details = {
            'hiddify_version': f'{hiddifypanel.__version__}',
            'python_version': f'{python_version}',
            'os_details': f'{platform()}',
            'user_agent': request.user_agent
        }
        return details

    def generate_github_issue_link_for_500_error(error, traceback, remove_sensetive_data=True, remove_unrelated_traceback_datails=True):

        def remove_sensetive_data_from_github_issue_link(issue_link):
            if hasattr(g, 'account') and hasattr(g.account, 'uuid') and g.account.uuid:
                issue_link.replace(f'{g.account.uuid}', '*******************')

            issue_link.replace(request.host, '**********')
            issue_link.replace(hconfig(ConfigEnum.proxy_path), '**********')
            issue_link.replace(hconfig(ConfigEnum.proxy_path_admin), '**********')
            issue_link.replace(hconfig(ConfigEnum.proxy_path_client), '**********')

        def remove_unrelated_traceback_details(stacktrace: str):
            lines = stacktrace.splitlines()
            if len(lines) < 1:
                return ""

            output = ''
            skip_next_line = False
            for i, line in enumerate(lines):
                if i == 0:
                    output += line + '\n'
                    continue
                if skip_next_line == True:
                    skip_next_line = False
                    continue
                if line.strip().startswith('File'):
                    if 'hiddify' in line.lower():
                        output += line + '\n'
                        if len(lines) > i+1:
                            output += lines[i + 1] + '\n'
                    skip_next_line = True

            return output

        if remove_unrelated_traceback_datails:
            traceback = remove_unrelated_traceback_details(traceback)

        issue_details = github_issue_details()

        issue_body = render_template('github_issue_body.j2', issue_details=issue_details, error=error, traceback=traceback)

        # Create github issue link
        issue_link = generate_github_issue_link(f"Internal server error: {error.name if hasattr(error,'name') and error.name != None and error.name else 'Unknown'}", issue_body)

        if remove_sensetive_data:
            remove_sensetive_data_from_github_issue_link(issue_link)

        return issue_link

    def generate_github_issue_link_for_admin_sidebar():

        issue_body = render_template('github_issue_body.j2', issue_details=github_issue_details())

        # Create github issue link
        issue_link = generate_github_issue_link('Please fill the title properly', issue_body)
        return issue_link

    app.jinja_env.globals['generate_github_issue_link_for_admin_sidebar'] = generate_github_issue_link_for_admin_sidebar
