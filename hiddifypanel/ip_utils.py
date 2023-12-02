from hiddifypanel.utils import get_interface_public_ip, get_socket_public_ip
import urllib

def get_ips(version):
    res = []
    i_ips = get_interface_public_ip(version)
    if i_ips:
        res = i_ips
    
    s_ip = get_socket_public_ip(version)
    if s_ip:
        res.append(s_ip)
    
    # send request
    try:
        ip = urllib.request.urlopen(f'https://v{version}.ident.me/').read().decode('utf8')
        if ip:
            res.append(ip)
    except:
        pass
    
    # remove duplicates
    return list(set(res))
