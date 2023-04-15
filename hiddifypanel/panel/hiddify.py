import socket
from sqlalchemy.orm import Load
from babel.dates import format_timedelta as babel_format_timedelta

from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _
import urllib
from hiddifypanel.models import *
from hiddifypanel.panel.database import db
import datetime
from flask import jsonify, g, url_for, Markup,abort
from wtforms.validators import ValidationError
from flask import flash as flask_flash
to_gig_d = 1000*1000*1000

from .hiddify2 import *
from .hiddify3 import *
def add_temporary_access():
    import random

    random_port = random.randint(30000, 50000)
    exec_command(
        f'/opt/hiddify-config/hiddify-panel/temporary_access.sh {random_port} &')
    # iptableparm=f'PREROUTING -p tcp --dport {random_port} -j REDIRECT --to-port 9000'
    # exec_command(f'iptables -t nat -I {iptableparm}')
    # exec_command(f'echo "iptables -t nat -D {iptableparm}" | at now + 4 hour')

    # iptableparm=f'INPUT -p tcp --dport {random_port} -j ACCEPT'
    # exec_command(f'iptables -I {iptableparm}')
    # exec_command(f'echo "iptables -D {iptableparm}" | at now + 4 hour')

    temp_admin_link = f"http://{get_ip(4)}:{random_port}{get_admin_path()}"
    g.temp_admin_link = temp_admin_link


def get_admin_path():
    proxy_path = hconfig(ConfigEnum.proxy_path)
        
    admin_secret=g.admin.uuid or get_super_admin_secret()
    return (f"/{proxy_path}/{admin_secret}/admin/")


def exec_command(cmd, cwd=None):
    try:
        import os
        os.system(cmd)
    except Exception as e:
        print(e)


def auth(function):
    def wrapper(*args, **kwargs):
        if g.user_uuid == None:
            return jsonify({"error": "auth failed"})
        if not admin and g.is_admin:
            return jsonify({"error": "admin can not access user page. add /admin/ to your url"})

        return function()

    return wrapper


def super_admin(function):
    def wrapper(*args, **kwargs):
        if g.admin.mode not in [AdminMode.super_admin]:
            abort(403,__("Access Denied"))
            return jsonify({"error": "auth failed"})

        return function(*args,**kwargs)

    return wrapper
def admin(function):
    def wrapper(*args, **kwargs):
        if g.admin.mode not in [AdminMode.admin,AdminMode.super_admin]:
            abort(_("Access Denied"),403)
            return jsonify({"error": "auth failed"})

        return function()

    return wrapper


def abs_url(path):
    return f"/{g.proxy_path}/{g.user_uuid}/{path}"


def asset_url(path):
    return f"/{g.proxy_path}/{path}"


def get_ip(version, retry=3):
    ip=None
    try:
        ip=urllib.request.urlopen(f'https://v{version}.ident.me/').read().decode('utf8')
    except:
        if retry > 0:
            ip= get_ip(version, retry=retry-1)
    return ip


def get_available_proxies(child_id):
    proxies = Proxy.query.filter(Proxy.child_id==child_id).all()

    if not hconfig(ConfigEnum.domain_fronting_domain,child_id):
        proxies = [c for c in proxies if 'Fake' not in c.cdn]
    if not hconfig(ConfigEnum.ssfaketls_enable,child_id):
        proxies = [c for c in proxies if 'faketls' != c.transport]
    if not hconfig(ConfigEnum.v2ray_enable,child_id):
        proxies = [c for c in proxies if 'v2ray' != c.proto]
    if not hconfig(ConfigEnum.shadowtls_enable,child_id):
        proxies = [c for c in proxies if c.transport != 'shadowtls']
    if not hconfig(ConfigEnum.ssr_enable,child_id):
        proxies = [c for c in proxies if 'ssr' != c.proto]
    if not hconfig(ConfigEnum.vmess_enable,child_id):
        proxies = [c for c in proxies if 'vmess' not in c.proto]

    if not hconfig(ConfigEnum.kcp_enable,child_id):
        proxies = [c for c in proxies if 'kcp' not in c.l3]

    if not hconfig(ConfigEnum.http_proxy_enable,child_id):
        proxies = [c for c in proxies if 'http' != c.l3]
    
    if not Domain.query.filter(Domain.mode.in_([DomainType.cdn,DomainType.auto_cdn_ip])).first():
        proxies = [c for c in proxies if c.cdn != "CDN"]

    proxies = [c for c in proxies if not ('vless' == c.proto and ProxyTransport.tcp ==c.transport and c.cdn==ProxyCDN.direct)]
    return proxies


def quick_apply_users():
    if hconfig(ConfigEnum.is_parent):
        return
    from hiddifypanel.panel import usage
    usage.update_local_usage()
    return
    # for user in User.query.all():
    #     if is_user_active(user):
    #         xray_api.add_client(user.uuid)
    #     else:
    #         xray_api.remove_client(user.uuid)

    exec_command("/opt/hiddify-config/install.sh apply_users &")
    import time
    time.sleep(1)
    return {"status": 'success'}



def flash_config_success(restart_mode='', domain_changed=True):

    if restart_mode:
        url = url_for('admin.Actions:reinstall', complete_install=restart_mode ==
                      'reinstall', domain_changed=domain_changed)
        apply_btn = f"<a href='{url}' class='btn btn-primary form_post'>" + \
            _("admin.config.apply_configs")+"</a>"
        flash((_('config.validation-success', link=apply_btn)), 'success')
    else:
        flash((_('config.validation-success-no-reset')), 'success')


# Importing socket library

# Function to display hostname and
# IP address

def get_domain_ip(domain,retry=3):
    import socket
    res=None
    try:
        res=socket.gethostbyname(domain)
        if not res:
            res= socket.getaddrinfo(domain, None, socket.AF_INET)[0][4][0]
    except:
         pass
    if not res:
        try:
            res= socket.getaddrinfo(domain, None, socket.AF_INET6)[0][4][0]
        except:
            pass
    
    if retry<=0:
        return None
    
    return res or get_domain_ip(domain,retry=retry-1)


def check_connection_to_remote(api_url):
    import requests
    path = f"{api_url}/api/v1/hello/"

    try:
        res = requests.get(path, verify=False, timeout=2).json()
        return True

    except:
        return False


def check_connection_for_domain(domain):
    import requests
    proxy_path = hconfig(ConfigEnum.proxy_path)
    admin_secret = hconfig(ConfigEnum.admin_secret)
    path = f"{proxy_path}/{admin_secret}/api/v1/hello/"
    try:
        print(f"https://{domain}/{path}")
        res = requests.get(
            f"https://{domain}/{path}", verify=False, timeout=10).json()
        return res['status'] == 200

    except:
        try:
            print(f"http://{domain}/{path}")
            res = requests.get(
                f"http://{domain}/{path}", verify=False, timeout=10).json()
            return res['status'] == 200
        except:
            try:
                print(f"http://{get_domain_ip(domain)}/{path}")
                res = requests.get(
                    f"http://{get_domain_ip(domain)}/{path}", verify=False, timeout=10).json()
                return res['status'] == 200
            except:
                return False
    return True


def get_user_link(uuid, domain, mode='',username=''):
    is_cdn= domain.mode == DomainType.cdn if type(domain)==Domain else False
    proxy_path = hconfig(ConfigEnum.proxy_path)
    res = ""
    if mode == "multi":
        res += "<div class='btn-group'>"
    d=domain.domain
    if "*" in d:
        d=d.replace("*",get_random_string(5,15))

    link = f"https://{d}/{proxy_path}/{uuid}/#{username}"
    if mode=="admin":
        link = f"https://{d}/{proxy_path}/{uuid}/admin/#{username}"
    link_multi = f"{link}multi"
    # if mode == 'new':
    #     link = f"{link}new"
    text = domain.alias or domain.domain
    color_cls='info'
    
    if type(domain)==Domain and domain.mode in [DomainType.cdn,DomainType.auto_cdn_ip]:
        auto_cdn=(domain.mode==DomainType.auto_cdn_ip) or (domain.cdn_ip and "MTN" in domain.cdn_ip)
        color_cls="success" if auto_cdn else 'warning'
        text = f'<span class="badge badge-secondary" >{"Auto" if auto_cdn else "CDN"}</span> '+text
        

    if mode == "multi":
        res += f"<a class='btn btn-xs btn-secondary' target='_blank' href='{link_multi}' >{_('all')}</a>"
    res += f"<a target='_blank' href='{link}' class='btn btn-xs btn-{color_cls} ltr' ><i class='fa-solid fa-arrow-up-right-from-square d-none'></i> {text}</a>"

    if mode == "multi":
        res += "</div>"
    return res


def flash(message, category):
    print(message)
    return flask_flash(Markup(message), category)


def validate_domain_exist(form, field):
    domain = field.data
    if not domain:
        return
    dip = get_domain_ip(domain)
    if dip == None:
        raise ValidationError(
            _("Domain can not be resolved! there is a problem in your domain"))


def reinstall_action(complete_install=False,domain_change=False):
    from hiddifypanel.admin.Actions import Actions
    action=Actions()
    return action.reinstall(complete_install=complete_install, domain_changed=domain_changed)

def check_need_reset(old_configs,do=False):
    restart_mode = ''
    for c in old_configs:
        if old_configs[c] != hconfig(c) and c.apply_mode():
            if restart_mode != 'reinstall':
                restart_mode = c.apply_mode()

    # do_full_install=old_config[ConfigEnum.telegram_lib]!=hconfig(ConfigEnum.telegram_lib)

    if not (do and restart_mode =='reinstall'):
        return flash_config_success(restart_mode=restart_mode, domain_changed=False)
        
    return reinstall_action(complete_install=True, domain_changed=domain_changed)
