

def add_or_update_domain(domain,ip,dns_type="A",proxied=True):
    if hconfig(ConfigEnum.cloudflare):
        cf=CloudFlare(token=hconfig(ConfigEnum.cloudflare))
        zone=get_zone(cf, domain)
        if zone:
            dns=get_dns(cf,zone,domain)        
            data={'name':domain[:-len(zone['name'])], 'type':dns_type, 'content':ip,'proxied':proxied}
            if dns:
                cf.zones.dns_records.post(zones['id'],dns['id'],data)
            else:
                cf.zones.dns_records.post(zones['id'],data)
            return True
    return False

def get_zone(cf,domain):
    zones= cf.zones.get();
    if not zones:return
    related_zone=[z for z in zones if z['name'] in domain]
    if not len(related_zone):return
    return related_zone[0]

def get_dns(cf,zone,domain):
    dns_rec=cf.zones.dns_records(zone['id'])
    rel_dns=[d for d in dns_rec if d['name']==domain]
    if not len(rel_dns):return 
    return rel_dns[0]