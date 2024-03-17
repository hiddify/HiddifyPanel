import user_agents
import datetime
import random
import re

from flask import render_template, request, Response, g
from apiflask import abort
from flask_classful import FlaskView, route
from urllib.parse import urlparse
from flask_babel import gettext as _


from hiddifypanel.auth import login_required
from hiddifypanel.database import db
from hiddifypanel.panel import hiddify
from hiddifypanel.models import *
from hiddifypanel import hutils


class UserView(FlaskView):

    @route('/useragent/')
    @login_required(roles={Role.user})
    def test(self):
        ua = request.user_agent.string
        print(ua)
        return ua

    def index(self):
        return self.auto_sub()

    def auto_sub(self):
        if g.user_agent['is_browser']:
            return self.new()
        return self.get_proper_config() or self.all_configs(base64=True)

    # former /sub/ or /sub (it was auto actually but we named it as /sub/)
    @route('/auto/')
    @route('/auto')
    @login_required(roles={Role.user})
    def force_sub(self):
        return self.get_proper_config() or self.all_configs(base64=False)

    # region new endpoints
    @route("/sub/")
    @route("/sub")
    @login_required(roles={Role.user})
    def sub(self):
        return self.all_configs(base64=False)

    @route("/sub64/")
    @route("/sub64")
    @login_required(roles={Role.user})
    def sub64(self):
        return self.all_configs(base64=True)

    @route("/xray/")
    @route("/xray")
    @login_required(roles={Role.user})
    def xray(self):
        c = c = get_common_data(g.account.uuid, mode="new")
        configs = hutils.proxy.xrayjson.configs_as_json(c['domains'], c['profile_title'])
        return add_headers(configs, c, 'application/json')

    @route("/singbox/")
    @route("/singbox")
    @login_required(roles={Role.user})
    def singbox_full(self):
        return self.full_singbox()

    @route("/singbox-ssh/")
    @route("/singbox-ssh")
    @login_required(roles={Role.user})
    def singbox_ssh(self):
        return self.singbox()

    @route("/clash/")
    @route("/clash")
    @login_required(roles={Role.user})
    def clash(self):
        return self.clash_config(meta_or_normal="normal")

    @route("/clashmeta/")
    @route("/clashmeta")
    @login_required(roles={Role.user})
    def clashmeta(self):
        return self.clash_config(meta_or_normal="meta")
    # endregion

    @ route('/new/')
    @ route('/new')
    @login_required(roles={Role.user})
    def new(self):
        conf = self.get_proper_config()
        if conf:
            return conf

        c = get_common_data(g.account.uuid, mode="new")
        user_agent = user_agents.parse(request.user_agent.string)
        # return render_template('home/multi.html', **c, ua=user_agent)
        return render_template('new.html', **c, ua=user_agent)

    def get_proper_config(self):
        if g.user_agent['is_browser']:
            return None
        ua = request.user_agent.string
        if g.user_agent['is_singbox'] or re.match('^(HiddifyNext|Dart|SFI|SFA)', ua, re.IGNORECASE):
            return self.full_singbox()

        if re.match('^(Clash-verge|Clash-?Meta|Stash|NekoBox|NekoRay|Pharos|hiddify-desktop)', ua, re.IGNORECASE):
            return self.clash_config(meta_or_normal="meta")
        if re.match('^(Clash|Stash)', ua, re.IGNORECASE):
            return self.clash_config(meta_or_normal="normal")

        # if 'HiddifyNext' in ua or 'Dart' in ua:
        #     return self.clash_config(meta_or_normal="meta")

        # if any([p in ua for p in ['FoXray', 'HiddifyNG','Fair%20VPN' ,'v2rayNG', 'SagerNet']]):
        if re.match('^(Hiddify|FoXray|Fair|v2rayNG|SagerNet|Shadowrocket|V2Box|Loon|Liberty)', ua, re.IGNORECASE):
            return self.all_configs(base64=True)

    @route('/clash/<meta_or_normal>/proxies.yml')
    @route('/clash/proxies.yml')
    @login_required(roles={Role.user})
    def clash_proxies(self, meta_or_normal="normal"):
        mode = request.args.get("mode")
        domain = request.args.get("domain", None)

        c = get_common_data(g.account.uuid, mode, filter_domain=domain)
        resp = Response(render_template('clash_proxies.yml',
                        meta_or_normal=meta_or_normal, **c))
        resp.mimetype = "text/plain"

        return resp

    # @ route('/report', methods=["POST"])
    # @login_required(roles={Role.user})
    # def report(self):

    #     # THE REPORT MODEL IS NOT COMPLETED YET.

    #     data = request.get_json()
    #     user_ip = hutils.network.auto_ip_selector.get_real_user_ip()
    #     report = Report()
    #     report.asn_id = hutils.network.auto_ip_selector.get_asn_id(user_ip)
    #     report.country = hutils.network.auto_ip_selector.get_country(user_ip)

    #     city_info = hutils.network.auto_ip_selector.get_city(user_ip)
    #     report.city = city_info['name']
    #     report.latitude = city_info['latitude']
    #     report.longitude = city_info['longitude']
    #     report.accuracy_radius = city_info['accuracy_radius']

    #     report.date = datetime.datetime.now()
    #     sub_update_time = data['sub_update_time']
    #     sub_url = data['sub_url']

    #     db.session.add(report)
    #     db.session.commit()
    #     proxy_map = {p.name: p.id for p in Proxy.query.all()}

    #     for name, ping in data['pings']:
    #         detail = ReportDetail()
    #         detail.report_id = report.id
    #         detail.proxy_id = proxy_map.get(name, -1)
    #         del proxy_map[name]
    #         if detail.proxy_id < 0:
    #             print("Error. Proxy not found!")
    #             continue
    #         detail.ping = ping
    #         db.session.add(detail)
    #     db.session.commit()

    @ route('/clash/<typ>.yml', methods=["GET", "HEAD"])
    @ route('/clash/<meta_or_normal>/<typ>.yml', methods=["GET", "HEAD"])
    @login_required(roles={Role.user})
    def clash_config(self, meta_or_normal="normal", typ="all.yml"):
        mode = request.args.get("mode")

        c = get_common_data(g.account.uuid, mode)

        hash_rnd = random.randint(0, 1000000)  # hash(f'{c}')
        if request.method == 'HEAD':
            resp = ""
        else:
            resp = render_template(
                'clash_config.yml', typ=typ, meta_or_normal=meta_or_normal, **c, hash=hash_rnd)

        return add_headers(resp, c)

    @ route('/full-singbox.json', methods=["GET", "HEAD"])
    @login_required(roles={Role.user})
    def full_singbox(self):
        mode = "new"  # request.args.get("mode")
        c = get_common_data(g.account.uuid, mode)
        # response.content_type = 'text/plain';
        if request.method == 'HEAD':
            resp = ""
        else:
            resp = hutils.proxy.singbox.configs_as_json(**c)

        return add_headers(resp, c, 'application/json')

    @ route('/singbox.json', methods=["GET", "HEAD"])
    @login_required(roles={Role.user})
    def singbox(self):
        if not hconfig(ConfigEnum.ssh_server_enable):
            return "SSH server is disable in settings"
        mode = "new"  # request.args.get("mode")
        c = get_common_data(g.account.uuid, mode)
        # response.content_type = 'text/plain';
        if request.method == 'HEAD':
            resp = ""
        else:
            resp = render_template('singbox_config.json', **c, host_keys=hutils.proxy.get_ssh_hostkeys(True),
                                   ssh_client_version=hiddify.get_ssh_client_version(user), ssh_ip=hutils.network.get_direct_host_or_ip(4), base64=False)

        return add_headers(resp, c)

    @route('/all.txt', methods=["GET", "HEAD"])
    @login_required(roles={Role.user})
    def all_configs(self, base64=False):
        mode = "new"  # request.args.get("mode")
        base64 = base64 or request.args.get("base64", "").lower() == "true"
        c = get_common_data(g.account.uuid, mode)
        # response.content_type = 'text/plain';
        if request.method == 'HEAD':
            resp = ""
        else:
            # render_template('all_configs.txt', **c, base64=hutils.encode.do_base_64)
            resp = hutils.proxy.xray.make_v2ray_configs(**c)

        if base64:
            resp = hutils.encode.do_base_64(resp)
        return add_headers(resp, c)

    @ route("/offline.html")
    @login_required(roles={Role.user})
    def offline():
        return f"Not Connected <a href='{hiddify.get_account_panel_link(g.account, request.host)}'>click for reload</a>"

    # backward compatiblity
    @route("/admin/<path:path>")
    @login_required()
    def admin(self, path):
        return ""


# def do_base_64(str):
#     import base64
#     resp = base64.b64encode(f'{str}'.encode("utf-8"))
#     return resp.decode()


# @cache.cache(ttl=300)
def get_domain_information(no_domain=False, filter_domain=None, alternative=None):
    domains = []
    default_asn = request.args.get("asn", '')
    if filter_domain:
        domain = filter_domain
        db_domain = Domain.query.filter(Domain.domain == domain).first() or Domain(
            domain=domain, mode=DomainType.direct, cdn_ip='', show_domains=[], child_id=0)
        domains = [db_domain]
    else:
        domain = alternative if not no_domain else None
        db_domain = Domain.query.filter(Domain.domain == domain).first()

        if not db_domain:
            parts = domain.split('.')  # TODO fix bug domain maybe null
            parts[0] = "*"
            domain_new = ".".join(parts)
            db_domain = Domain.query.filter(Domain.domain == domain_new).first()

        if not db_domain:
            db_domain = Domain(domain=domain, show_domains=[])
            hutils.flask.flash(_("This domain does not exist in the panel!" + domain))

        domains = db_domain.show_domains or Domain.query.filter(Domain.sub_link_only != True).all()

    has_auto_cdn = False
    for d in domains:
        db.session.expunge(d)
        d.has_auto_ip = False
        if d.mode == DomainType.auto_cdn_ip or d.cdn_ip:
            has_auto_cdn = True
            d.has_auto_ip = d.mode == DomainType.auto_cdn_ip or (
                d.cdn_ip and "MTN" in d.cdn_ip)
            d.cdn_ip = hutils.network.auto_ip_selector.get_clean_ip(
                d.cdn_ip, d.mode == DomainType.auto_cdn_ip, default_asn)
            # print("autocdn ip mode ", d.cdn_ip)
        if "*" in d.domain:
            d.domain = d.domain.replace("*", hutils.random.get_random_string(5, 15))

    if len(domains) == 0:
        domains = [Domain(id=0, domain=alternative, mode=DomainType.direct, cdn_ip='', show_domains=[], child_id=0)]
        domains[0].has_auto_ip = True

    return domains, db_domain, has_auto_cdn


def get_common_data(user_uuid, mode, no_domain=False, filter_domain=None):
    '''Usable for user account'''
    # uuid_secret=str(uuid.UUID(user_secret))
    domains, db_domain, has_auto_cdn = get_domain_information(no_domain, filter_domain, request.host)

    domain = db_domain.domain
    user: User = g.account if g.account.uuid == user_uuid else User.by_uuid(f'{user_uuid}')
    if user is None:
        abort(401, "Invalid User")

    package_mode_dic = {
        UserMode.daily: 1,
        UserMode.weekly: 7,
        UserMode.monthly: 30

    }

    expire_days = user.remaining_days
    reset_days = user.days_to_reset()
    if reset_days >= expire_days:
        reset_days = 1000

    expire_s = int((datetime.date.today() + datetime.timedelta(days=expire_days) - datetime.date(1970, 1, 1)).total_seconds())

    user_ip = hutils.network.auto_ip_selector.get_real_user_ip()
    asn = hutils.network.auto_ip_selector.get_asn_short_name(user_ip)
    profile_title = f'{db_domain.alias or db_domain.domain} {user.name}'
    profile_url = hiddify.get_account_panel_link(user, request.host)
    if has_auto_cdn and asn != 'unknown':
        profile_title += f" {asn}"

    return {
        # 'direct_host':direct_host,
        'profile_title': profile_title,
        'user': user,
        'user_activate': user.is_active,
        'domain': domain,
        'mode': mode,
        'fake_ip_for_sub_link': datetime.datetime.now().strftime(f"%H.%M--%Y.%m.%d.time:%H%M"),
        'usage_limit_b': int(user.usage_limit_GB * 1024 * 1024 * 1024),
        'usage_current_b': int(user.current_usage_GB * 1024 * 1024 * 1024),
        'expire_s': expire_s,
        'expire_days': expire_days,
        'expire_rel': hutils.convert.format_timedelta(datetime.timedelta(days=expire_days)),
        'reset_day': reset_days,
        'hconfigs': get_hconfigs(),
        'hdomains': get_hdomains(),
        'ConfigEnum': ConfigEnum,
        'link_maker': hutils.proxy,
        'domains': domains,
        "bot": g.get('bot', None),
        "db_domain": db_domain,
        "telegram_enable": hiddify.is_telegram_proxy_enable(domains),
        "ip": user_ip,
        "ip_debug": hutils.network.auto_ip_selector.get_real_user_ip_debug(user_ip),
        "asn": asn,
        "country": hutils.network.auto_ip_selector.get_country(user_ip),
        'has_auto_cdn': has_auto_cdn,
        'profile_url': profile_url
    }


def add_headers(res, c, mimetype="text/plain"):
    resp = Response(res)
    resp.mimetype = mimetype
    resp.headers['Subscription-Userinfo'] = f"upload=0;download={c['usage_current_b']};total={c['usage_limit_b']};expire={c['expire_s']}"
    resp.headers['profile-web-page-url'] = request.base_url.rsplit('/', 1)[0].replace("http://", "https://") + "/"

    if hconfig(ConfigEnum.branding_site):
        resp.headers['support-url'] = hconfig(ConfigEnum.branding_site)
    resp.headers['profile-update-interval'] = 1
    # resp.headers['content-disposition']=f'attachment; filename="{c["db_domain"].alias or c["db_domain"].domain} {c["user"].name}"'

    resp.headers['profile-title'] = 'base64:' + hutils.encode.do_base_64(c['profile_title'])

    return resp
