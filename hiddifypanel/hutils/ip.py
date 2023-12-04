import random
import socket
import ipaddress
from typing import List, Literal, Union
import netifaces
import urllib
import ipaddress
from hiddifypanel.cache import cache


def get_domain_ip(domain: str, retry: int = 3, version: Literal[4, 6] = None) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address, None]:
    res = None
    if not version:
        try:
            res = socket.gethostbyname(domain)
        except:
            pass

    if not res and version != 6:
        try:
            res = socket.getaddrinfo(domain, None, socket.AF_INET)[0][4][0]
        except:
            pass

    if not res and version != 4:
        try:
            res = f"[{socket.getaddrinfo(domain, None, socket.AF_INET6)[0][4][0]}]"

            res = res[1:-1]

        except:
            pass

    if retry <= 0 or not res:
        return None
    
    return ipaddress.ip_address(res) or get_domain_ip(domain, retry=retry-1) if res else None


def get_socket_public_ip(version: Literal[4, 6]) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address, None]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if version == 6:
            s.connect(("2001:4860:4860::8888", 80))
        else:
            s.connect(("8.8.8.8", 80))
        ip_address = ipaddress.ip_address(s.getsockname()[0])
        s.close()
        return ip_address if ip_address.is_global else None
    except socket.error:
        return None


def get_interface_public_ip(version: Literal[4, 6]) -> List[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]:
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
                    address = ipaddress.ip_address(addr['addr'])
                    if address.is_global:
                        addresses.append(address)

        return addresses

    except (OSError, KeyError):
        return []


@cache.cache(ttl=600)
def get_ips(version: Literal[4, 6]) -> List[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]:
    addrs = []
    i_ips = get_interface_public_ip(version)
    if i_ips:
        addrs = i_ips

    s_ip = get_socket_public_ip(version)
    if s_ip:
        addrs.append(s_ip)

    # send request
    try:
        ip = urllib.request.urlopen(f'https://v{version}.ident.me/').read().decode('utf8')
        if ip:
            addrs.append(ipaddress.ip_address(ip))
    except:
        pass

    # remove duplicates
    return list(set(addrs))


@cache.cache(ttl=600)
def get_ip(version: Literal[4, 6], retry: int = 5) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address]:
    ips = get_interface_public_ip(version)
    ip = None
    if ips:
        ip = random.sample(ips, 1)[0]

    if ip is None:
        ip = get_socket_public_ip(version)

    if ip is None:
        try:
            ip = urllib.request.urlopen(f'https://v{version}.ident.me/').read().decode('utf8')
            if ip:
                ip = ipaddress.ip_address(ip)
        except:
            pass
    if ip is None and retry > 0:
        ip = get_ip(version, retry=retry-1)
    return ip
