
from flask import abort, render_template, request, Response, g, url_for, jsonify, flash
from wtforms.validators import Regexp, ValidationError
import urllib
import uuid
import datetime
from hiddifypanel.models import *
from hiddifypanel.panel.database import db
from hiddifypanel.panel import hiddify, clean_ip

from . import link_maker
from flask_classful import FlaskView, route
import random
from urllib.parse import urlparse
import user_agents
from flask_babelex import gettext as _


class UserView(FlaskView):

    # @route('/old')
    # @route('/old/')
    # def index(self):

    #     c=get_common_data(g.user_uuid,mode="")
    #     user_agent =  user_agents.parse(request.user_agent.string)

    #     return render_template('home/index.html',**c,ua=user_agent)
    # @route('/multi/')
    # @route('/multi')
    # def multi(self):

    #     c=get_common_data(g.user_uuid,mode="multi")

    #     user_agent =  user_agents.parse(request.user_agent.string)

    #     return render_template('home/multi.html',**c,ua=user_agent)

    @route('/new/')
    @route('/new')
    @route('/')
    def new(self):

        c = get_common_data(g.user_uuid, mode="new")

        user_agent = user_agents.parse(request.user_agent.string)

        return render_template('home/multi.html', **c, ua=user_agent)

    @route('/clash/<meta_or_normal>/proxies.yml')
    @route('/clash/proxies.yml')
    def clash_proxies(self, meta_or_normal="normal"):
        mode = request.args.get("mode")
        domain = request.args.get("domain", None)

        c = get_common_data(g.user_uuid, mode, filter_domain=domain)
        resp = Response(render_template('clash_proxies.yml', meta_or_normal=meta_or_normal, **c))
        resp.mimetype = "text/plain"

        return resp

    @route('/clash/<typ>.yml', methods=["GET", "HEAD"])
    @route('/clash/<meta_or_normal>/<typ>.yml', methods=["GET", "HEAD"])
    def clash_config(self, meta_or_normal="normal", typ="all.yml"):
        mode = request.args.get("mode")

        c = get_common_data(g.user_uuid, mode)

        hash_rnd = random.randint(0, 1000000)  # hash(f'{c}')
        if request.method == 'HEAD':
            resp = Response("")
        else:
            resp = Response(render_template('clash_config.yml', typ=typ, meta_or_normal=meta_or_normal, **c, hash=hash_rnd))
        resp.mimetype = "text/plain"
        resp.headers['Subscription-Userinfo'] = f"upload=0;download={c['usage_current_b']};total={c['usage_limit_b']};expire={c['expire_s']}"
        resp.headers['profile-web-page-url'] = request.base_url.split("clash")[0].replace("http://", "https://")
        if hconfig(ConfigEnum.branding_site):
            resp.headers['support-url'] = hconfig(ConfigEnum.branding_site)
        resp.headers['profile-update-interval'] = 1

        profile_title = f'{c["db_domain"].alias or c["db_domain"].domain} {c["user"].name}'
        if c['has_auto_cdn']:
            profile_title += f" {c['asn']}"
        resp.headers['profile-title'] = 'base64:'+do_base_64(profile_title)
        return resp

    @route('/all.txt', methods=["GET", "HEAD"])
    def all_configs(self):
        mode = "new"  # request.args.get("mode")
        base64 = request.args.get("base64", "").lower() == "true"
        c = get_common_data(g.user_uuid, mode)
        # response.content_type = 'text/plain';
        if request.method == 'HEAD':
            resp = ""
        else:
            resp = render_template('all_configs.txt', **c, base64=do_base_64)

        res = ""
        for line in resp.split("\n"):
            if "vmess://" in line:
                line = "vmess://"+do_base_64(line.replace("vmess://", ""))
            res += line+"\n"
        if base64:
            res = do_base_64(res)
        resp = Response(res)
        resp.mimetype = "text/plain"
        resp.headers['Subscription-Userinfo'] = f"upload=0;download={c['usage_current_b']};total={c['usage_limit_b']};expire={c['expire_s']}"
        resp.headers['profile-web-page-url'] = request.base_url.split("all.txt")[0].replace("http://", "https://")
        if hconfig(ConfigEnum.branding_site):
            resp.headers['support-url'] = hconfig(ConfigEnum.branding_site)
        resp.headers['profile-update-interval'] = 1
        # resp.headers['content-disposition']=f'attachment; filename="{c["db_domain"].alias or c["db_domain"].domain} {c["user"].name}"'
        profile_title = f'{c["db_domain"].alias or c["db_domain"].domain} {c["user"].name}'
        if c['has_auto_cdn']:
            profile_title += f" {c['asn']}"
        resp.headers['profile-title'] = 'base64:'+do_base_64(profile_title)

        return resp

    @route('/manifest.webmanifest')
    def create_pwa_manifest(self):

        domain = urlparse(request.base_url).hostname
        name = (domain if g.is_admin else g.user.name)
        return jsonify({
            "name": f"Hiddify {name}",
            "short_name": f"{name}"[:12],
            "theme_color": "#f2f4fb",
            "background_color": "#1a1b21",
            "display": "standalone",
            "scope": f"/",
            "start_url": f"https://{domain}"+url_for("admin.Dashboard:index" if g.is_admin else "user2.UserView:new_1")+"?pwa=true",
            "description": "Hiddify, for a free Internet",
            "orientation": "any",
            "icons": [
                {
                    "src": url_for('static', filename='images/hiddify-dark.png'),
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "maskable any"
                }
            ]
        })

    @route("/offline.html")
    def offline():
        return f"Not Connected <a href='/{hconfig(ConfigEnum.proxy_path)}/{g.user.uuid}/'>click for reload</a>"


def do_base_64(str):
    import base64
    resp = base64.b64encode(f'{str}'.encode("utf-8"))
    return resp.decode()


def get_common_data(user_uuid, mode, no_domain=False, filter_domain=None):
    mode = "new"
    default_asn = request.args.get("asn")
    if filter_domain:
        domain = filter_domain
        db_domain = Domain.query.filter(Domain.domain == domain).first() or Domain(domain=domain, mode=DomainType.direct, cdn_ip='', show_domains=[], child_id=0)
        domains = [db_domain]
    else:
        domain = urlparse(request.base_url).hostname if not no_domain else None
        DB = ParentDomain if hconfig(ConfigEnum.is_parent) else Domain
        db_domain = DB.query.filter(DB.domain == domain).first()

        if not db_domain:
            parts = domain.split('.')
            parts[0] = "*"
            domain_new = ".".join(parts)
            db_domain = DB.query.filter(DB.domain == domain_new).first()

        if not db_domain:
            db_domain = DB(domain=domain, show_domains=[])
            print("no domain")
            flash(_("This domain does not exist in the panel!" + domain))

        if mode == 'multi':
            domains = Domain.query.all()
        elif mode == 'new':
            # db_domain=Domain.query.filter(Domain.domain==domain).first()
            domains = db_domain.show_domains or Domain.query.filter(Domain.sub_link_only != True).all()
        else:

            domains = [db_domain]
            direct_host = domain

            # if db_domain and db_domain.mode==DomainType.cdn:
            #     direct_domain_db=Domain.query.filter(Domain.mode==DomainType.direct).first()
            # if not direct_domain_db:
            #     direct_host=urllib.request.urlopen('https://v4.ident.me/').read().decode('utf8')
            #     direct_domain_db=Domain(domain=direct_host,mode=DomainType.direct)

            # domains.append(direct_domain_db)

    # uuid_secret=str(uuid.UUID(user_secret))
    user = User.query.filter(User.uuid == f'{user_uuid}').first()
    if user is None:
        abort(401, "Invalid User")

    has_auto_cdn = False
    for d in domains:
        db.session.expunge(d)
        d.has_auto_ip = False
        if d.mode == DomainType.auto_cdn_ip or d.cdn_ip:
            has_auto_cdn = True
            d.has_auto_ip = d.mode == DomainType.auto_cdn_ip or (d.cdn_ip and "MTN" in d.cdn_ip)
            d.cdn_ip = clean_ip.get_clean_ip(d.cdn_ip, d.mode == DomainType.auto_cdn_ip, default_asn)
            print("autocdn ip mode ", d.cdn_ip)
        if "*" in d.domain:
            d.domain = d.domain.replace("*", hiddify.get_random_string(5, 15))

    package_mode_dic = {
        UserMode.daily: 1,
        UserMode.weekly: 7,
        UserMode.monthly: 30

    }
    bot = None
    if hconfig(ConfigEnum.license):
        from hiddifypanel.panel.telegrambot import bot

    g.locale = hconfig(ConfigEnum.lang)
    expire_days = remaining_days(user)
    reset_days = days_to_reset(user)
    # print(reset_days)
    # raise
    if reset_days >= expire_days:
        reset_days = 1000
    # print(reset_days,expire_days,reset_days<=expire_days)
    expire_s = int((datetime.date.today()+datetime.timedelta(days=expire_days)-datetime.date(1970, 1, 1)).total_seconds())

    user_ip = clean_ip.get_real_user_ip()
    return {
        # 'direct_host':direct_host,
        'user': user,
        'user_activate': is_user_active(user),
        'domain': domain,
        'mode': mode,
        'fake_ip_for_sub_link': datetime.datetime.now().strftime(f"%H.%M--%Y.%m.%d.time:%H%M"),
        'usage_limit_b': int(user.usage_limit_GB*1024*1024*1024),
        'usage_current_b': int(user.current_usage_GB*1024*1024*1024),
        'expire_s': expire_s,
        'expire_days': expire_days,
        'expire_rel': hiddify.format_timedelta(datetime.timedelta(days=expire_days)),
        'reset_day': reset_days,
        'hconfigs': get_hconfigs(),
        'hdomains': get_hdomains(),
        'ConfigEnum': ConfigEnum,
        'link_maker': link_maker,
        'domains': domains,
        "bot": bot,
        "db_domain": db_domain,
        "telegram_enable": hconfig(ConfigEnum.telegram_enable) and any([d for d in domains if d.mode in [DomainType.direct, DomainType.relay, DomainType.old_xtls_direct]]),
        "ip": user_ip,
        "ip_debug": clean_ip.get_real_user_ip_debug(user_ip),
        "asn": clean_ip.get_asn_short_name(user_ip),
        "country": clean_ip.get_country(user_ip),
        'has_auto_cdn': has_auto_cdn
    }
