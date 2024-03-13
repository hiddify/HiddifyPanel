import CloudFlare
from hiddifypanel.models import hconfig, ConfigEnum


def add_or_update_domain(domain, ip, dns_type="A", proxied=True):
    res = False
    if hconfig(ConfigEnum.cloudflare):
        cf = CloudFlare.CloudFlare(token=hconfig(ConfigEnum.cloudflare))
        zone = get_zone(cf, domain)
        if zone:
            dns = get_dns(cf, zone, domain)
            data = {'name': domain[:-len(zone['name'])], 'type': dns_type, 'content': ip, 'proxied': proxied}
            if dns:
                cf.zones.dns_records.put(zone['id'], dns['id'], data=data)
            else:
                cf.zones.dns_records.post(zone['id'], data=data)
            res = True
    return res


def get_zone(cf, domain):
    zones = cf.zones.get()
    res = ""
    if zones:
        related_zone = [z for z in zones if z['name'] in domain]
        if len(related_zone):
            res = related_zone[0]
    return res


def get_dns(cf, zone, domain):
    dns_rec = cf.zones.dns_records(zone['id'])
    rel_dns = [d for d in dns_rec if d['name'] == domain]
    res = ""
    if len(rel_dns):
        res = rel_dns[0]
    return res
