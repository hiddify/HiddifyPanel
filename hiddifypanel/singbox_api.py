import xtlsapi
from hiddifypanel.models import *


def get_singbox_client():
    if hconfig(ConfigEnum.is_parent):
        return
    return xtlsapi.SingboxClient('127.0.0.1', 10086)


def get_enabled_users():
    if hconfig(ConfigEnum.is_parent):
        return


def get_inbound_tags():
    if hconfig(ConfigEnum.is_parent):
        return
    try:
        xray_client = get_singbox_client()
        inbounds = [inb.name.split(">>>")[1] for inb in xray_client.stats_query('inbound')]
        print(f"Success in get inbound tags {inbounds}")
    except Exception as e:
        print(f"error in get inbound tags {e}")
        inbounds = []
    return list(set(inbounds))


def add_client(uuid):
    if hconfig(ConfigEnum.is_parent):
        return
    raise NotImplementedError()


def remove_client(uuid):
    if hconfig(ConfigEnum.is_parent):
        return
    raise NotImplementedError()


def get_usage(uuid, reset=False):
    if hconfig(ConfigEnum.is_parent):
        return
    xray_client = get_singbox_client()
    d = xray_client.get_client_download_traffic(f'{uuid}@hiddify.com', reset=reset)
    u = xray_client.get_client_upload_traffic(f'{uuid}@hiddify.com', reset=reset)
    print(f"Success {uuid} d={d} u={u}")
    res = None
    if d is None:
        res = u
    elif u is None:
        res = d
    else:
        res = d + u
    return res
