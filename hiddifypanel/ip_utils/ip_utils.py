import random
import socket
import ipaddress
import netifaces
import urllib

from hiddifypanel.models.domain import Domain, DomainType
from hiddifypanel.cache import cache

def normalize_ipv6(address):
    if type(address) == str and len(address) > 0:
        if address[0] == '[' and address[-1] == ']':
            return address[1:-1]

    return address

def are_ipv6_addresses_equal(address1, address2):
    try:
        address1 = normalize_ipv6(address1)
        address2 = normalize_ipv6(address2)

        ipv6_addr1 = ipaddress.ip_address(address1)
        ipv6_addr2 = ipaddress.ip_address(address2)

        return ipv6_addr1 == ipv6_addr2

    except ValueError as e:
        print(f"Invalid IPv6 address: {e}")
        return False


def get_domain_ip(dom, retry=3, version=None):

    res = None
    if not version:
        try:
            res = socket.gethostbyname(dom)
        except:
            pass

    if not res and version != 6:
        try:
            res = socket.getaddrinfo(dom, None, socket.AF_INET)[0][4][0]
        except:
            pass

    if not res and version != 4:
        try:
            res = f"[{socket.getaddrinfo(dom, None, socket.AF_INET6)[0][4][0]}]"
        except:
            pass

    if retry <= 0:
        return None

    return res or get_domain_ip(dom, retry=retry-1)


def get_socket_public_ip(version):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if version == 6:
            s.connect(("2001:4860:4860::8888", 80))
        else:
            s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()

        return ip_address if is_public_ip(ip_address) else None
    except socket.error:
        return None


def is_public_ip(address):
    if address.startswith('127.') or address.startswith('169.254.') or address.startswith('10.') or address.startswith('192.168.') or address.startswith('172.'):
        return False
    if address.startswith('fe80:') or address.startswith('fd') or address.startswith('fc00:'):
        return False
    if address.startswith('::') or address.startswith('fd') or address.startswith('fc00:'):
        return False
    return True


def get_interface_public_ip(version):
    addresses = []
    try:
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            if version == 4:
                address_info = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
            elif version == 6:
                address_info = netifaces.ifaddresses(interface).get(netifaces.AF_INET6, [])
            else:
                continue

            if address_info:
                for addr in address_info:
                    address = addr['addr']
                    if (is_public_ip(address)):
                        addresses.append(address)

        return addresses

    except (OSError, KeyError):
        return []

@cache.cache(ttl=600)
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

@cache.cache(ttl=600)
def get_ip(version, retry=5):
    ips = get_interface_public_ip(version)
    ip = None
    if (ips):
        ip = random.sample(ips, 1)[0]

    if ip is None:
        ip = get_socket_public_ip(version)

    if ip is None:
        try:
            ip = urllib.request.urlopen(f'https://v{version}.ident.me/').read().decode('utf8')

        except:
            pass
    if ip is None and retry > 0:
        ip = get_ip(version, retry=retry-1)
    return ip