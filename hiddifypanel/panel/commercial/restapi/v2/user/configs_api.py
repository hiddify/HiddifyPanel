from urllib.parse import urlparse
from flask import g, request
from flask import current_app as app
from flask.views import MethodView
from hiddifypanel.auth import login_required
from hiddifypanel.models import Proxy, Role, ConfigEnum, hconfig
from apiflask import Schema
from apiflask.fields import String
from hiddifypanel.panel.user.user import get_common_data
from hiddifypanel import hutils


class ConfigSchema(Schema):
    name = String(required=True)
    domain = String(required=True)
    link = String(required=True)
    protocol = String(required=True)
    transport = String(required=True)
    security = String(required=True)
    type = String(required=True)


class AllConfigsAPI(MethodView):
    decorators = [login_required({Role.user})]

    @app.output(ConfigSchema(many=True))  # type: ignore
    def get(self):
        def create_item(name, domain, type, protocol, transport, security, link):
            dto = ConfigSchema()
            dto.name = name
            dto.type = type
            dto.domain = domain
            dto.protocol = protocol
            dto.transport = transport
            dto.security = security
            dto.link = link
            return dto

        items = []
        base_url = f"https://{urlparse(request.base_url).hostname}/{g.proxy_path}/{g.account.uuid}/"
        c = get_common_data(g.account.uuid, 'new')
        config_name = hutils.encode.url_encode(c['user'].name)

        # Add Auto
        items.append(
            create_item(
                "Auto", "ALL", "", "", "", "",
                # f"{base_url}sub/?asn={c['asn']}"
                f"{base_url}auto/?asn={c['asn']}#{config_name}"
            )
        )

        if hconfig(ConfigEnum.sub_full_singbox_enable):
            # Add Full Singbox
            items.append(
                create_item(
                    "Full Singbox", "ALL", "", "", "", "",
                    # f"{base_url}full-singbox.json?asn={c['asn']}"
                    f"{base_url}singbox/?asn={c['asn']}#{config_name}"
                )
            )

        if hconfig(ConfigEnum.sub_full_xray_json_enable):
            # Add Full Xray
            items.append(
                create_item(
                    "Full Xray", "ALL", "", "", "", "",
                    f"{base_url}xray/#{config_name}"
                )
            )

        if hconfig(ConfigEnum.sub_full_links_enable):
            # Add Subscription link
            items.append(
                create_item(
                    "Subscription link", "ALL", "", "", "", "",
                    # f"{base_url}all.txt?name={c['db_domain'].alias or c['db_domain'].domain}-{c['asn']}&asn={c['asn']}&mode={c['mode']}"
                    f"{base_url}sub/?asn={c['asn']}#{config_name}"
                )
            )

        if hconfig(ConfigEnum.sub_full_links_b64_enable):
            # Add Subscription link base64
            items.append(
                create_item(
                    "Subscription link b64", "ALL", "", "", "", "",
                    # f"{base_url}all.txt?name=new_link_{c['db_domain'].alias or c['db_domain'].domain}-{c['asn']}-{c['mode']}&asn={c['asn']}&mode={c['mode']}&base64=True"
                    f"{base_url}sub64/?asn={c['asn']}#{config_name}"
                )
            )
        if hconfig(ConfigEnum.sub_full_clash_meta_enable):
            # Add Clash Meta
            items.append(
                create_item(
                    "Clash Meta", "ALL", "", "", "", "",
                    # f"clashmeta://install-config?url={base_url}clash/meta/all.yml&name=mnormal_{c['db_domain'].alias or c['db_domain'].domain}-{c['asn']}-{c['mode']}&asn={c['asn']}&mode={c['mode']}"
                    f"{base_url}clashmeta/?asn={c['asn']}#{config_name}"
                )
            )

        if hconfig(ConfigEnum.sub_full_clash_enable):
            # Add Clash
            items.append(
                create_item(
                    "Clash", "ALL", "Except VLess", "", "", "",
                    # f"clash://install-config?url={base_url}clash/all.yml&name=new_normal_{c['db_domain'].alias or c['db_domain'].domain}-{c['asn']}-{c['mode']}&asn={c['asn']}&mode={c['mode']}"
                    f"{base_url}clash/?asn={c['asn']}#{config_name}"
                )
            )

        if hconfig(ConfigEnum.wireguard_enable):
            items.append(
                create_item(
                    "Wireguard", "Wireguard", "", "", "", "",
                    # f"{base_url}singbox.json?name={c['db_domain'].alias or c['db_domain'].domain}-{c['asn']}&asn={c['asn']}&mode={c['mode']}"
                    f"{base_url}wireguard/#{config_name}"
                )
            )
            # Add Singbox: SSh
        if hconfig(ConfigEnum.sub_singbox_ssh_enable) and hconfig(ConfigEnum.ssh_server_enable):
            items.append(
                create_item(
                    "Singbox: SSH", "SSH", "", "", "", "",
                    # f"{base_url}singbox.json?name={c['db_domain'].alias or c['db_domain'].domain}-{c['asn']}&asn={c['asn']}&mode={c['mode']}"
                    f"{base_url}singbox-ssh/?asn={c['asn']}#{config_name}"
                )
            )

        for pinfo in hutils.proxy.get_valid_proxies(c['domains']):
            items.append(
                create_item(
                    pinfo["name"].replace("_", " "),
                    f"{'Auto ' if pinfo['dbdomain'].has_auto_ip else ''}{pinfo['mode']}",
                    pinfo['server'],
                    pinfo['proto'],
                    pinfo['transport'],
                    pinfo['l3'],
                    f"{hutils.proxy.xray.to_link(pinfo)}"
                )
            )

        return items
