import CloudFlare
from hiddifypanel.models import hconfig, ConfigEnum

__cf: CloudFlare.CloudFlare = ''  # type: ignore


def __prepare_cf_api_client() -> bool:
    '''Prepares cloudflare client if it's not already'''
    global __cf
    if __cf and isinstance(__cf, CloudFlare.CloudFlare):
        return True

    if hconfig(ConfigEnum.cloudflare):
        __cf = CloudFlare.CloudFlare(token=hconfig(ConfigEnum.cloudflare))
        if __cf and isinstance(__cf, CloudFlare.CloudFlare):
            return True
    return False


def add_or_update_dns_record(domain: str, ip: str, dns_type: str = "A", proxied: bool = True) -> bool:
    '''This function cloud throw an exception'''
    if not __prepare_cf_api_client():
        return False

    zone_name = __extract_root_domain(domain)
    zone = __get_zone(zone_name)
    if zone:
        record = __get_dns_record(zone, domain)
        dns_name = domain[:-len(zone['name'])].replace('.', '')
        # if the input domain is root itself
        dns_name = '@' if not dns_name else dns_name
        data = {
            'name': dns_name,
            'type': dns_type, 'content': ip, 'proxied': proxied
        }
        if not record:
            api_res = __cf.zones.dns_records.post(zone['id'], data=data)
        else:
            api_res = __cf.zones.dns_records.put(zone['id'], record['id'], data=data)

        # validate api response
        if api_res['name'] == domain and api_res['type'] == dns_type and api_res['content'] == ip:
            return True
    return False


def delete_dns_record(domain: str) -> bool:
    '''Deletes a DNS record from cloudflare panel of user'''
    if not __prepare_cf_api_client():
        return False

    zone_name = __extract_root_domain(domain)
    zone = __get_zone(zone_name)
    record = __get_dns_record(zone, domain)
    if zone and record:
        api_res = __cf.zones.dns_records.delete(zone['id'], record['id'])
        if api_res['id'] == record['id']:
            return True
    return False


def __get_zone(zone_name: str) -> dict | None:
    zones = __cf.zones.get()
    for z in zones:
        if z['name'] == zone_name:
            return z
    return None


def __get_dns_record(zone, domain: str) -> dict | None:
    '''Returns dns record if exists'''
    dns_records = __cf.zones.dns_records(zone['id'])
    for r in dns_records:
        if r['name'] == domain:
            return r
    return None


def __extract_root_domain(domain: str) -> str:
    domain_parts = domain.split(".")
    if len(domain_parts) > 1:
        return ".".join(domain_parts[-2:])
    else:
        return domain
