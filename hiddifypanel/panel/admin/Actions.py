import urllib.request
import json
from flask_classful import FlaskView, route
from flask import render_template, request, redirect, g
from hiddifypanel.hutils.flask import hurl_for
from hiddifypanel.auth import login_required
from flask import current_app as app
from flask_babel import gettext as _


from hiddifypanel import hutils
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify, usage
from hiddifypanel.panel.run_commander import commander, Command


class Actions(FlaskView):

    @login_required(roles={Role.super_admin})
    def index(self):
        return render_template('index.html')

    @login_required(roles={Role.super_admin})
    def viewlogs(self):
        log_files = hutils.flask.list_dir_files(f"{app.config['HIDDIFY_CONFIG_PATH']}log/system/")
        return render_template('view_logs.html', log_files=log_files)

    @login_required(roles={Role.super_admin})
    @route('apply_configs', methods=['POST'])
    def apply_configs(self):
        return self.reinstall(False)

    @route('reset', methods=['POST'])
    @login_required(roles={Role.super_admin})
    def reset(self):
        return self.reset2()

    @login_required(roles={Role.super_admin})
    def reset2(self):
        res = render_template("result.html",
                              out_type="info",
                              out_msg="",
                              log_file_url=get_log_api_url(),
                              log_file='restart.log',
                              show_success=True,
                              domains=get_domains())

        # run restart.sh
        commander(Command.restart_services)

        return res

    @login_required(roles={Role.super_admin})
    @route('reinstall', methods=['POST'])
    def reinstall(self, complete_install=True, domain_changed=False):
        return self.reinstall2(complete_install, domain_changed)

    @login_required(roles={Role.super_admin})
    def reinstall2(self, complete_install=True, domain_changed=False):
        if int(hconfig(ConfigEnum.db_version)) < 9:
            return ("Please update your panel before this action.")
        if hutils.node.is_child():
            hutils.node.run_node_op_in_bg(hutils.node.child.sync_with_parent)

        domain_changed = request.args.get("domain_changed", str(domain_changed)).lower() == "true"
        complete_install = request.args.get("complete_install", str(complete_install)).lower() == "true"
        if domain_changed:
            hutils.flask.flash((_('domain.changed_in_domain_warning')), 'info')
        # hutils.flask.flash(f'complete_install={complete_install} domain_changed={domain_changed} ', 'info')
        # return render_template("result.html")
        # hiddify.add_temporary_access()
        file = "install.sh" if complete_install else "apply_configs.sh"
        try:
            server_ip = urllib.request.urlopen('https://v4.ident.me/').read().decode('utf8')
        except BaseException:
            server_ip = "server_ip"

        admin_links = f"<h5 >{_('Admin Links')}</h5><ul>"

        admin_links += f"<li><span class='badge badge-danger'>{_('Not Secure')}</span>: <a class='badge ltr share-link' href='{hiddify.get_account_panel_link(g.account, server_ip,is_https=False)}'>{hiddify.get_account_panel_link(g.account, server_ip,is_https=False)}</a></li>"
        domains = Domain.get_domains()
        # domains=[*domains,f'{server_ip}.sslip.io']

        for d in domains:
            link = hiddify.get_account_panel_link(g.account, d)
            admin_links += f"<li><a target='_blank' class='badge ltr' href='{link}'>{link}</a></li>"

        resp = render_template("result.html",
                               out_type="info",
                               out_msg=_("admin.waiting_for_update") +
                               admin_links,
                               log_file_url=get_log_api_url(),
                               log_file="0-install.log",
                               show_success=True,
                               domains=get_domains())

        # subprocess.Popen(f"sudo {config['HIDDIFY_CONFIG_PATH']}/{file} --no-gui".split(" "), cwd=f"{config['HIDDIFY_CONFIG_PATH']}", start_new_session=True)

        # run install.sh or apply_configs.sh
        commander(Command.install if complete_install else Command.apply)

        # import time
        # time.sleep(1)
        return resp

    @login_required(roles={Role.super_admin})
    def change_reality_keys(self):
        key = hutils.crypto.generate_x25519_keys()
        set_hconfig(ConfigEnum.reality_private_key, key['private_key'])
        set_hconfig(ConfigEnum.reality_public_key, key['public_key'])
        hutils.flask.flash_config_success(restart_mode=ApplyMode.apply_config, domain_changed=False)
        return redirect(hurl_for('admin.SettingAdmin:index'))

    @ login_required(roles={Role.super_admin})
    def status(self):
        # run status.sh
        commander(Command.status)
        return render_template("result.html",
                               out_type="info",
                               out_msg=_("see the log in the bellow screen"),
                               log_file_url=get_log_api_url(),
                               log_file="status.log",
                               show_success=False,
                               domains=get_domains())

    @ route('update', methods=['POST'])
    @ login_required(roles={Role.super_admin})
    def update(self):
        return self.update2()

    def update2(self):
        # hiddify.add_temporary_access()
        # run update.sh

        commander(Command.update)

        return render_template("result.html",
                               out_type="success",
                               out_msg=_("Success! Please wait around 5 minutes to make sure everything is updated."),
                               show_success=True,
                               log_file_url=get_log_api_url(),
                               log_file="update.log",
                               domains=get_domains())

    def get_some_random_reality_friendly_domain(self):
        test_domain = request.args.get("test_domain")
        import ping3
        from hiddifypanel.hutils.network.auto_ip_selector import IPASN, IPCOUNTRY
        ipv4 = hutils.network.get_ip_str(4)
        server_country = (IPCOUNTRY.get(ipv4) or {}).get('country', {}).get('iso_code', 'unknown')
        server_asn = (IPASN.get(ipv4) or {}).get('autonomous_system_organization', 'unknown')
        res = "<table><tr><th>Domain</th><th>IP</th><th>Country</th><th>ASN</th><th>Ping (ms)</th><th>TCP ping (ms)</th></tr>"
        res += f"<tr><td>Your Server</td><td>{ipv4}</td><td>{server_country}</td><td>{server_asn}</td><td>0</td></tr>"
        import time
        start = time.time()
        for d in [test_domain, *hutils.network.get_random_domains(30)]:
            if not d:
                continue
            if time.time() - start > 20:
                break

            tcp_ping = hutils.network.is_domain_reality_friendly(d)
            if tcp_ping:
                dip = str(hutils.network.get_domain_ip(d))
                dip_country = (IPCOUNTRY.get(dip) or {}).get('country', {}).get('iso_code', 'unknown')
                if dip_country == "IR":
                    continue
                response_time = -1
                try:
                    response_time = ping3.ping(d, unit='ms')
                    if response_time:
                        response_time = int(response_time)
                except BaseException:
                    pass
                dip_asn = (IPASN.get(dip) or {}).get('autonomous_system_organization', 'unknown')
                res += f"<tr><td>{d}</td><td>{dip}</td><td>{dip_country}</td><td>{dip_asn}</td><td>{response_time}</td><td>{tcp_ping}<td></tr>"

        return res + "</table>"

    @ login_required(roles={Role.super_admin})
    def update_usage(self):
        color = 'white' if g.darkmode else 'black'
        return render_template("result.html",
                               out_type="info",
                               out_msg=f'<pre class="ltr" style="color:{color};">{json.dumps(usage.update_local_usage(),indent=2)}</pre>',
                               log_file_url=None
                               )


def get_log_api_url():
    return f'/{g.get("new_proxy_path",g.proxy_path)}/api/v2/admin/log/'


def get_domains():
    return [str(d.domain).replace("*", hutils.random.get_random_string(3, 6)) for d in Domain.get_domains(always_add_all_domains=True, always_add_ip=False)]
