import datetime
import uuid
import json
import os
import click
from dateutil import relativedelta


from hiddifypanel import hutils

from hiddifypanel.models import *
from hiddifypanel.panel import hiddify, usage
from hiddifypanel.database import db
from hiddifypanel.panel.init_db import init_db


def drop_db():
    """Cleans database"""
    db.drop_all()


def downgrade():
    if (hconfig(ConfigEnum.db_version) >= "49"):
        set_hconfig(ConfigEnum.db_version, '42', commit=False)
        StrConfig.query.filter(StrConfig.key.in_([ConfigEnum.tuic_enable, ConfigEnum.tuic_port, ConfigEnum.hysteria_enable,
                               ConfigEnum.hysteria_port, ConfigEnum.ssh_server_enable, ConfigEnum.ssh_server_port, ConfigEnum.ssh_server_redis_url])).delete()
        Proxy.query.filter(Proxy.l3.in_([ProxyL3.ssh, ProxyL3.h3_quic, ProxyL3.custom])).delete()
        db.session.commit()
        os.rename("/opt/hiddify-manager/hiddify-panel/hiddifypanel.db.old", "/opt/hiddify-manager/hiddify-panel/hiddifypanel.db")


def backup():
    dbdict = hiddify.dump_db_to_dict()
    os.makedirs('backup', exist_ok=True)
    dst = f'backup/{datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S")}.json'
    with open(dst, 'w') as fp:
        json.dump(dbdict, fp, indent=4, sort_keys=True, default=str)

    if hconfig(ConfigEnum.telegram_bot_token):
        from hiddifypanel.panel.commercial.telegrambot import bot, register_bot
        if not bot.token:
            register_bot(True)

        with open(dst, 'rb') as document:
            for admin in AdminUser.query.filter(AdminUser.mode == AdminMode.super_admin, AdminUser.telegram_id is not None).all():
                caption = ("Backup \n" + admin_links())
                bot.send_document(admin.telegram_id, document, visible_file_name=dst.replace("backup/", ""), caption=caption[:min(len(caption), 1000)])


def all_configs():
    valid_users = [u.to_dict(dump_id=True) for u in User.query.filter((User.usage_limit > User.current_usage)).all() if u.is_active]
    host_child_ids = [c.id for c in Child.query.filter(Child.mode == ChildMode.virtual).all()]
    configs = {
        "users": valid_users,
        "domains": [u.to_dict(dump_ports=True, dump_child_id=True) for u in Domain.query.filter(Domain.child_id.in_(host_child_ids)).all() if "*" not in u.domain],
        # "parent_domains": [hiddify.parent_domain_dict(u) for u in ParentDomain.query.all()],
        # "hconfigs": get_hconfigs(json=True),
        "chconfigs": get_hconfigs_childs(host_child_ids, json=True)
    }

    def_user = None if len(User.query.all()) > 1 else User.query.filter(User.name == 'default').first()
    domains = Domain.query.all()
    sslip_domains = [d.domain for d in domains if "sslip.io" in d.domain]

    configs['chconfigs'][0]['first_setup'] = def_user is not None and len(sslip_domains) > 0
    server_ip = hutils.network.get_ip_str(4)
    owner = AdminUser.get_super_admin()

    configs['admin_path'] = hiddify.get_account_panel_link(owner, server_ip, is_https=False, prefere_path_only=True)
    configs['panel_links'] = []
    configs['panel_links'].append(hiddify.get_account_panel_link(owner, server_ip, is_https=False))
    configs['panel_links'].append(hiddify.get_account_panel_link(owner, server_ip))
    domains = get_panel_domains()

    for d in domains:
        configs['panel_links'].append(hiddify.get_account_panel_link(owner, d.domain))

    print(json.dumps(configs, indent=4))


def update_usage():
    print(usage.update_local_usage())


def test():
    print(ConfigEnum("auto_update1"))


def admin_links():

    server_ip = hutils.network.get_ip_str(4)
    owner = AdminUser.get_super_admin()

    admin_links = f"Not Secure (do not use it - only if others not work):\n   {hiddify.get_account_panel_link(owner, server_ip,is_https=True)}\n"

    domains = get_panel_domains()
    admin_links += f"Secure:\n"
    if not any([d for d in domains if 'sslip.io' not in d.domain]):
        admin_links += f"   (not signed) {hiddify.get_account_panel_link(owner, server_ip)}\n"

    for d in domains:
        admin_links += f"   {hiddify.get_account_panel_link(owner, d.domain)}\n"

    print(admin_links)
    return admin_links


def admin_path():
    admin = AdminUser.get_super_admin()
    # WTF is the owner and server_id?
    domain = get_panel_domains()[0]
    print(hiddify.get_account_panel_link(admin, domain, prefere_path_only=True))


# def get_this_host_domains():
#     current_child_ids


def hysteria_domain_port():
    if not hconfig(ConfigEnum.hysteria_enable):
        return
    out = []
    for i, domain in enumerate(Domain.query.filter(Domain.mode.in_([DomainType.direct, DomainType.relay, DomainType.fake])).all()):
        out.append(f"{domain.domain}:{int(hconfig(ConfigEnum.hysteria_port))+domain.id}")
    print(";".join(out))


def tuic_domain_port():
    if not hconfig(ConfigEnum.tuic_enable):
        return
    out = []
    for i, domain in enumerate(Domain.query.filter(Domain.mode.in_([DomainType.direct, DomainType.relay, DomainType.fake])).all()):
        out.append(f"{domain}:{int(hconfig(ConfigEnum.tuic_port))+domain.id}")
    print(";".join(out))


def init_app(app):
    # add multiple commands in a bulk
    # print(app.config['SQLALCHEMY_DATABASE_URI'] )
    for command in [hysteria_domain_port, tuic_domain_port, init_db, drop_db, all_configs, update_usage, test, admin_links, admin_path, backup, downgrade]:
        app.cli.add_command(app.cli.command()(command))

    @ app.cli.command()
    @ click.option("--domain", "-d")
    def add_domain(domain):
        # TODO: Fix this
        if Domain.query.filter(Domain.domain == domain).first():
            return "Domain already exist."
        d = Domain(domain=domain)
        if not hutils.node.is_parent():
            d.mode = DomainType.direct
        db.session.add(d)
        db.session.commit()
        return "success"

    @ app.cli.command()
    @ click.option("--admin_secret", "-a")
    def set_admin_secret(admin_secret):
        StrConfig.query.filter(StrConfig.key == ConfigEnum.admin_secret).update({'value': admin_secret})
        db.session.commit()
        return "success"

    @ app.cli.command()
    @ click.option("--key", "-k")
    @ click.option("--val", "-v")
    def set_setting(key, val):
        old_hconfigs = get_hconfigs()
        hiddify.add_or_update_config(key=key, value=val)

        return "success"

    @ app.cli.command()
    @ click.option("--config", "-c")
    def import_config(config):
        next10year = datetime.date.today() + relativedelta.relativedelta(years=10)
        data = []
        if "USER_SECRET" in config:
            secrets = config["USER_SECRET"].split(";")
            for i, s in enumerate(secrets):
                data.append(User(name=f"default {i}", uuid=uuid.UUID(s), usage_limit_GB=9000, package_days=3650))

        if "MAIN_DOMAIN" in config:
            domains = config["MAIN_DOMAIN"].split(";")
            for i, d in enumerate(domains):
                if not Domain.query.filter(Domain.domain == d).first():
                    data.append(Domain(domain=d, mode=DomainType.direct),)

        strmap = {
            "TELEGRAM_FAKE_TLS_DOMAIN": ConfigEnum.telegram_fakedomain,
            "TELEGRAM_SECRET": ConfigEnum.shared_secret,
            "SS_FAKE_TLS_DOMAIN": ConfigEnum.ssfaketls_fakedomain,
            "FAKE_CDN_DOMAIN": ConfigEnum.domain_fronting_domain,
            "BASE_PROXY_PATH": ConfigEnum.proxy_path,
            "ADMIN_SECRET": ConfigEnum.admin_secret,
            "TELEGRAM_AD_TAG": ConfigEnum.telegram_adtag
        }
        boolmap = {
            "ENABLE_SS": ConfigEnum.ssfaketls_enable,
            "ENABLE_TELEGRAM": ConfigEnum.telegram_enable,
            "ENABLE_VMESS": ConfigEnum.vmess_enable,
            # "ENABLE_MONITORING":ConfigEnum.ssfaketls_enable,
            "ENABLE_FIREWALL": ConfigEnum.firewall,
            "ENABLE_NETDATA": ConfigEnum.netdata,
            "ENABLE_HTTP_PROXY": ConfigEnum.http_proxy_enable,
            "ALLOW_ALL_SNI_TO_USE_PROXY": ConfigEnum.allow_invalid_sni,
            "ENABLE_AUTO_UPDATE": ConfigEnum.auto_update,
            "ENABLE_SPEED_TEST": ConfigEnum.speed_test,
            "BLOCK_IR_SITES": ConfigEnum.block_iran_sites,
            "ONLY_IPV4": ConfigEnum.only_ipv4
        }

        for k in config:
            if k in strmap:
                if hconfig(strmap[k]) is None:
                    data.append(StrConfig(key=strmap[k], value=config[k]))
                else:
                    StrConfig.query.filter(StrConfig.key == strmap[k]).update({
                        'value': config[k]
                    })
            if k in boolmap:
                if hconfig(boolmap[k]) is None:
                    data.append(BoolConfig(key=boolmap[k], value=config[k]))
                else:
                    BoolConfig.query.filter(BoolConfig.key == strmap[k]).update({
                        'value': config[k]
                    })
        if len(data):
            db.session.bulk_save_objects(data)
        db.session.commit()

    @ app.cli.command()
    @ click.option("--xui_db_path", "-x")
    def xui_importer(xui_db_path):
        try:
            hutils.importer.xui.import_data(xui_db_path)
            print('success')
        except Exception as e:
            print(f'failed to import xui data: Error: {e}')
