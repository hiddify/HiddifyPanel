import traceback
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

from apiflask import APIFlask, HTTPError, abort


def init_app(app: APIFlask):
    app.jinja_env.globals['ConfigEnum'] = ConfigEnum
    app.jinja_env.globals['DomainType'] = DomainType
    app.jinja_env.globals['UserMode'] = UserMode
    app.jinja_env.globals['hconfig'] = hconfig
    app.jinja_env.globals['g'] = g

    @app.errorhandler(Exception)
    def internal_server_error(e):
        # print(request.headers)
        last_version = hiddify.get_latest_release_version('hiddifypanel')  # TODO: add dev update check
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

            last_version = hiddify.get_latest_release_version('hiddifypanel')  # TODO: add dev update check
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

    @app.spec_processor
    def set_default_path_values(spec):
        for path in spec['paths'].values():
            for operation in path.values():
                if 'parameters' in operation:
                    for parameter in operation['parameters']:
                        if parameter['name'] == 'proxy_path':
                            parameter['schema'] = {'type': 'string', 'default': g.proxy_path}
                        # elif parameter['name'] == 'user_secret':
                        #     parameter['schema'] = {'type': 'string', 'default': g.account_uuid}
        return spec

    @app.url_value_preprocessor
    def pull_secret_code(endpoint, values):
        # just remove proxy_path
        # by doing that we don't need to get proxy_path in every view function, we have it in g.proxy_path. it's done in base_middleware function
        if values:
            values.pop('proxy_path', None)
            # values.pop('admin_uuid', None)

    @app.url_defaults
    def add_proxy_path_user(endpoint, values):
        if 'proxy_path' not in values:

            if isinstance(g.account, AdminUser):
                values['proxy_path'] = hconfig(ConfigEnum.proxy_path_admin)
            # elif 'static' in endpoint:
            #     values['proxy_path'] = hconfig(ConfigEnum.proxy_path)
            elif hiddify.is_user_panel_call():
                values['proxy_path'] = hconfig(ConfigEnum.proxy_path_client)
            else:
                values['proxy_path'] = hconfig(ConfigEnum.proxy_path_admin)

        if hiddify.is_api_v1_call(endpoint=endpoint) and 'admin_uuid' not in values:
            values['admin_uuid'] = get_super_admin_uuid()

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

    @app.before_request
    def backward_compatibility_middleware():
        # get needed variables
        proxy_path = hiddify.get_proxy_path_from_url(request.url)
        if not proxy_path:
            abort(400, "invalid")
        user_agent = user_agents.parse(request.user_agent.string)
        # need this variable in redirect_to_new_format view
        g.user_agent = user_agent
        if user_agent.is_bot:
            abort(400, "invalid")

        # get proxy paths
        deprecated_proxy_path = hconfig(ConfigEnum.proxy_path)
        admin_proxy_path = hconfig(ConfigEnum.proxy_path_admin)
        client_proxy_path = hconfig(ConfigEnum.proxy_path_client)

        incorrect_request = False
        new_link = ''

        # handle deprecated proxy path
        if proxy_path == deprecated_proxy_path:
            incorrect_request = True
            # request.url = request.url.replace('http://', 'https://')
            if hiddify.is_admin_panel_call(deprecated_format=True):
                new_link = f'https://{request.host}/{admin_proxy_path}/admin/'
            elif hiddify.is_user_panel_call(deprecated_format=True):
                new_link = f'https://{request.host}/{client_proxy_path}/'
            elif hiddify.is_api_call(request.path):
                if hiddify.is_admin_api_call():
                    new_link = request.url.replace(deprecated_proxy_path, admin_proxy_path)
                elif hiddify.is_user_api_call():
                    new_link = request.url.replace(deprecated_proxy_path, client_proxy_path)
                else:
                    return abort(400, 'invalid request')
            else:
                return abort(400, 'invalid request')

        # handle uuid url format
        if uuid := hutils.utils.get_uuid_from_url_path(request.path):
            if not hiddify.is_telegram_call():
                incorrect_request = True
                account = get_user_by_uuid(uuid) or get_admin_by_uuid(uuid) or abort(400, 'invalid request')
                if new_link:
                    if hiddify.is_api_call(request.path):
                        new_link = new_link.replace(f'/{uuid}', '')
                    new_link = hutils.utils.add_basic_auth_to_url(new_link, account.username, account.password)
                else:
                    if hiddify.is_api_call(request.path):
                        new_link = request.url.replace(f'/{uuid}', '')
                        new_link = hutils.utils.add_basic_auth_to_url(new_link, account.username, account.password)
                    else:
                        new_link = f'https://{account.username}:{account.password}@{request.host}/{proxy_path}/'
                        if "/admin/" in request.path:
                            new_link += "admin/"

        if incorrect_request:
            new_link = new_link.replace('http://', 'https://')
            # if request made by a browser, show new format page else redirect to new format
            # redirect api calls always
            if not hiddify.is_api_call(request.path) and user_agent.browser:
                return render_template('redirect_to_new_format.html', new_link=new_link)
            return redirect(new_link, 301)

    @app.before_request
    def base_middleware():
        if request.endpoint == 'static' or request.endpoint == "videos":
            return

        # validate request made by human (just check user agent, there's no capcha)
        g.user_agent = user_agents.parse(request.user_agent.string)
        if g.user_agent.is_bot:
            abort(400, "invalid")

        # validate proxy path

        g.proxy_path = hutils.utils.get_proxy_path_from_url(request.url)
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
            'user_agent': 'Unknown'
        }
        if hasattr(g, 'user_agent') and str(g.user_agent):
            details['user_agent'] = g.user_agent.ua_string
        return details

    def generate_github_issue_link_for_500_error(error, traceback, remove_sensetive_data=True, remove_unrelated_traceback_datails=True):

        def remove_sensetive_data_from_github_issue_link(issue_link):
            if hasattr(g, 'acount') and hasattr(g.account, 'uuid') and g.account.uuid:
                issue_link.replace(f'{g.account.uuid}', '*******************')
            deprecated_proxy_path = hconfig(ConfigEnum.proxy_path)
            admin_proxy_path = hconfig(ConfigEnum.proxy_path_admin)
            client_proxy_path = hconfig(ConfigEnum.proxy_path_client)
            if deprecated_proxy_path:
                issue_link.replace(deprecated_proxy_path, '**********')
            if admin_proxy_path:
                issue_link.replace(admin_proxy_path, '**********')
            if client_proxy_path:
                issue_link.replace(client_proxy_path, '**********')

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
