import traceback
import user_agents
from flask import render_template, request, jsonify, redirect
from flask import g, send_from_directory, session, Markup
from flask_babelex import gettext as _
import hiddifypanel
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify, github_issue_generator
from sys import version as python_version
from platform import platform
import hiddifypanel.panel.authentication as auth
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

    @app.url_defaults
    def add_proxy_path_user(endpoint, values):

        if 'user_secret' not in values and hasattr(g, 'user_uuid'):
            values['user_secret'] = f'{g.account_uuid}'
        if 'proxy_path' not in values:
            # values['proxy_path']=f'{g.proxy_path}'
            values['proxy_path'] = hconfig(ConfigEnum.proxy_path)

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
    def base_middleware():
        if request.endpoint == 'static' or request.endpoint == "videos":
            return

        # validate request made by human (just check user agent, there's no capcha)
        g.user_agent = user_agents.parse(request.user_agent.string)
        if g.user_agent.is_bot:
            abort(400, "invalid")

        # validate proxy path
        g.proxy_path = hutils.utils.get_proxy_path_from_url(request.url)
        if not g.proxy_path:
            abort(400, "invalid")
        if g.proxy_path != hconfig(ConfigEnum.proxy_path):
            if app.config['DEBUG']:
                abort(400, Markup(
                    f"Invalid Proxy Path <a href=/{hconfig(ConfigEnum.proxy_path)}/{get_super_admin_secret()}/admin>admin</a>"))
            abort(400, "Invalid Proxy Path")

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
            if (not telegrambot.bot) or (not telegrambot.bot.username):
                telegrambot.register_bot()
            g.bot = telegrambot.bot
        else:
            g.bot = None

    @app.before_request
    def api_auth_middleware():
        '''In every api request(whether is for the admin or the user) the client should provide api key and we check it'''
        if 'api' not in request.path:  # type: ignore
            return

        # get authenticated account
        account: AdminUser | User | None = auth.standalone_api_auth_verify()
        if not account:
            return abort(401)
        # get account role
        role = auth.get_account_role(account)
        if not role:
            return abort(401)
        # setup authenticated account things (uuid, is_admin, etc.)
        g.account = account
        g.account_uuid = account.uuid
        g.is_admin = False if role == auth.AccountRole.user else True

    @app.before_request
    def backward_compatibility_middleware():
        if hutils.utils.is_uuid_in_url_path(request.path):
            # check that if proxy path is valid or not. because don't want to redirect to admin panel if client provided a non-sense proxy path
            if g.proxy_path != hconfig(ConfigEnum.proxy_path):
                # this will make a fingerprint for panel. should redirect the request to decoy website.
                # abort(400, "invalid proxy path")
                redirect(hconfig(ConfigEnum.decoy_domain), code=301)

            uuid = hutils.utils.get_uuid_from_url_path(request.path) or abort(400, 'invalid request')
            if '/api/' in request.path:
                return redirect(f"{request.url.replace('http://','https://').replace(uuid,'').replace('//','/')}", code=301)  # type: ignore

            if '/admin/' in request.path:
                # check if there is such uuid or not, because don't want to redirect to admin panel if there is no such uuid
                # otherwise anyone can provide any secret to get access to admin panel
                if not get_admin_by_uuid(uuid):
                    abort(400, 'invalid request')
                admin_link = f'{request.url_root.replace("http://", "https://").rstrip("/")}/{g.proxy_path}/admin/'
                if g.user_agent.get_browser():
                    return render_template('redirect_to_admin.html', admin_link=admin_link), 302
                else:
                    return redirect(admin_link, code=301)
            else:
                user = get_user_by_uuid(uuid) or abort(400, 'invalid request')
                user_link = f'{request.url_root.replace("http", "https").rstrip("/")}/{g.proxy_path}/#{user.name}'  # type: ignore
                if g.user_agent.get_browser():
                    return render_template('redirect_to_user.html', user_link=user_link), 302
                else:
                    return redirect(user_link, code=301)

    @app.before_request
    def basic_auth_middleware():
        '''if the request is for user panel(user page), we try to authenticate the user with basic auth or the client session data, we do that for admin panel too'''
        if 'api' in request.path:  # type: ignore
            return

        account: AdminUser | User | None = None

        # if we don't have endpoint, we can't detect the request is for admin panel or user panel, so we can't authenticate
        if not request.endpoint:
            abort(400, "invalid request")

        if request.endpoint and 'UserView' in request.endpoint:
            account = auth.standalone_user_basic_auth_verification()
        else:
            account = auth.standalone_admin_basic_auth_verification()
        # get authenticated account
        if not account:
            return abort(401)

        # TODO: if the client is not authenticate, redirect to login page

        # get account role
        role = auth.get_account_role(account)
        if not role:
            return abort(401)
        # setup authenticated account things (uuid, is_admin, etc.)
        g.account = account
        g.account_uuid = account.uuid
        g.is_admin = False if role == auth.AccountRole.user else True

    # @app.auth_required(basic_auth, roles=['super_admin', 'admin', 'agent', 'user'])

    @app.url_value_preprocessor
    def pull_secret_code(endpoint, values):
        # just remove proxy_path
        # by doing that we don't need to get proxy_path in every view function, we have it in g.proxy_path. it's done in base_middleware function
        if values:
            values.pop('proxy_path', None)
            values.pop('user_secret', None)

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
            if hasattr(g, 'user_uuid') and g.account_uuid:
                issue_link.replace(f'{g.account_uuid}', '*******************')
            if hconfig(ConfigEnum.proxy_path) and hconfig(ConfigEnum.proxy_path):
                issue_link.replace(hconfig(ConfigEnum.proxy_path), '**********')

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
