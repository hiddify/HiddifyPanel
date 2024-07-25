import glob
from typing import List, Literal, Set, Union
from urllib.parse import urlparse
import urllib.request
import ipaddress
from hiddifypanel.hutils.network.auto_ip_selector import IPASN
import netifaces
import requests
import random
import socket
import time
import ssl
import re
import os


from hiddifypanel.models import *
from hiddifypanel.cache import cache


def get_domain_ip(domain: str, retry: int = 3, version: Literal[4, 6] | None = None) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address, None]:
    res = None
    if not version:
        try:
            res = socket.gethostbyname(domain)
        except BaseException:
            pass

    if not res and version != 6:
        try:
            res = socket.getaddrinfo(domain, None, socket.AF_INET)[0][4][0]
        except BaseException:
            pass

    if not res and version != 4:
        try:
            res = f"{socket.getaddrinfo(domain, None, socket.AF_INET6)[0][4][0]}"

        except BaseException:
            pass

    if retry <= 0:
        return None
    if not res:
        return get_domain_ip(domain, retry=retry - 1, version=version)

    return ipaddress.ip_address(res)


def get_domain_ips(domain: str, retry: int = 3) -> Set[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]:
    res = set()
    if retry < 0:
        return res
    try:
        _, _, ips = socket.gethostbyname_ex(domain)
        for ip in ips:
            res.add(ipaddress.ip_address(ip))
    except Exception:
        pass

    try:
        for ip in socket.getaddrinfo(domain, None, socket.AF_INET):
            res.add(ipaddress.ip_address(ip[4][0]))
    except BaseException:
        pass

    try:
        for ip in socket.getaddrinfo(domain, None, socket.AF_INET6):
            res.add(ipaddress.ip_address(ip[4][0]))
    except BaseException:
        pass

    return res or get_domain_ips(domain, retry=retry - 1)


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
def get_ips(version: Literal[4, 6] | None = None) -> List[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]:
    if not version:
        return [*get_ips(4), *get_ips(6)]
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
    except BaseException:
        pass

    # remove duplicates
    return list(set(addrs))


@cache.cache(ttl=600)
def get_ip_str(version: Literal[4, 6], retry: int = 5) -> str | None:
    ip = get_ip(version, retry)
    if ip is None:
        return None
    return str(ip)


@cache.cache(ttl=600)
def get_ip(version: Literal[4, 6], retry: int = 5) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
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
        except BaseException:
            pass
    if ip is None and retry > 0:
        ip = get_ip(version, retry=retry - 1)
    return ip


def get_random_domains(count: int = 1, retry: int = 3) -> List[str]:
    try:
        irurl = "https://api.ooni.io/api/v1/measurements?probe_cc=IR&test_name=web_connectivity&anomaly=false&confirmed=false&failure=false&order_by=test_start_time&limit=1000"
        # cnurl="https://api.ooni.io/api/v1/measurements?probe_cc=CN&test_name=web_connectivity&anomaly=false&confirmed=false&failure=false&order_by=test_start_time&limit=1000"
        data_ir = requests.get(irurl).json()
        # data_cn=requests.get(url).json()

        domains = [urlparse(d['input']).netloc.lower() for d in data_ir['results'] if d['scores']['blocking_country'] == 0.0]
        domains = [d for d in domains if not d.endswith(".ir") and ".gov" not in d]

        return random.sample(domains, count)
    except Exception as e:
        print('Error, getting random domains... ', e, 'retrying...', retry)
        if retry <= 0:
            defdomains = ["fa.wikipedia.org", 'en.wikipedia.org', 'wikipedia.org', 'yahoo.com', 'en.yahoo.com']
            print('Error, using default domains')
            return random.sample(defdomains, count)
        return get_random_domains(count, retry - 1)


# not used
def is_domain_support_tls_13(domain: str) -> bool:
    context = ssl.create_default_context()
    port = 433
    with socket.create_connection((domain, port)) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            return ssock.version() == "TLSv1.3"


def is_domain_support_h2_tls13(sni: str, server: str = '') -> bool:
    try:

        context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        context.options |= (ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
        context.options |= ssl.OP_NO_COMPRESSION
        context.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")
        context.set_alpn_protocols(["h2"])
        start_time = time.monotonic()
        with socket.create_connection((server or sni, 443), timeout=2) as sock:

            with context.wrap_socket(sock, server_hostname=sni) as ssock:
                elapsed_time = time.monotonic() - start_time
                valid = ssock.version() == "TLSv1.3"
                if valid:
                    if int(max(1, elapsed_time * 1000)):
                        return True
                return False
    except Exception as e:
        print(f'{sni} {e}')
        return False


def is_domain_reality_friendly(domain: str) -> bool:
    return is_domain_support_h2_tls13(domain)


def fallback_domain_compatible_with_servernames(fallback_domain: str, servername: str) -> bool:
    return is_domain_support_h2_tls13(servername, fallback_domain)


def get_random_decoy_domain() -> str:
    for _ in range(10):
        domains = get_random_domains(10)
        for d in domains:
            if is_domain_use_letsencrypt(d):
                return d

    return "bbc.com"


def is_domain_use_letsencrypt(domain: str) -> bool:
    """
    This function is used to filter the payment and big companies to
    avoid phishing detection
    """
    try:
        # Create a socket connection to the website
        with socket.create_connection((domain, 443)) as sock:
            context = ssl.create_default_context()
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                certificate = ssock.getpeercert()

        issuer = dict(x[0] for x in certificate.get("issuer", []))

        return issuer['organizationName'] == "Let's Encrypt"
    except BaseException:
        return False


@cache.cache(ttl=300)
def get_direct_host_or_ip(prefer_version: int) -> str:
    from hiddifypanel.models import Domain
    direct = Domain.query.filter(Domain.mode == DomainType.direct, Domain.sub_link_only == False).first()
    if not direct:
        direct = Domain.query.filter(Domain.mode == DomainType.direct).first()
    if direct:
        return direct.domain

    direct = get_ip_str(prefer_version)
    if direct:
        return direct

    return get_ip_str(4 if prefer_version == 6 else 6)


# not used
def get_warp_info() -> str:
    proxies = dict(http='socks5://127.0.0.1:3000',
                   https='socks5://127.0.0.1:3000')
    res = requests.get("https://cloudflare.com/cdn-cgi/trace", proxies=proxies, timeout=1).text

    dicres = {line.split("=")[0]: line.split("=")[0] for line in res}
    return str(dicres)


def is_ssh_password_authentication_enabled() -> bool:
    def check_file(file_path: str) -> bool:
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as f:
                    for line in f.readlines():
                        line = line.strip()
                        if line.startswith('#'):
                            continue
                        if re.search(r"^PasswordAuthentication\s+no", line, re.IGNORECASE):
                            return False
            except Exception as e:
                print(e)

        return True

    for config_file in glob.glob("/etc/ssh/sshd*") + glob.glob("/etc/ssh/sshd*/*"):
        if not check_file(config_file):
            return False

    return True


def is_out_of_range_port(port: int) -> bool:
    return port < 1 or port > 65535


def add_number_to_ipv4(ip: str, number: int) -> str:
    octets = list(map(int, ip.split('.')))

    octets[2] = (octets[2] + (octets[3] + number) // 256)
    octets[3] = (octets[3] + number) % 256

    return f"{octets[0]}.{octets[1]}.{octets[2]}.{octets[3]}"


def add_number_to_ipv6(ip: str, number: int) -> str:
    segments = ip.split(':')

    # Increment the last segment by the specified number
    segments[-1] = hex(int(segments[-1] or "0", 16) + number)[2:]

    # Join the segments back together with colons
    modified_ipv6 = ":".join(segments)

    return modified_ipv6


@ cache.cache(600)
def is_in_same_asn(domain_or_ip: str, domain_or_ip_target: str) -> bool:
    '''Returns True if domain is in panel ASN'''
    try:
        ip = domain_or_ip if is_ip(domain_or_ip) else get_domain_ip(domain_or_ip)
        ip_target = domain_or_ip_target if is_ip(domain_or_ip_target) else get_domain_ip(domain_or_ip_target)

        if not ip or not ip_target:
            return False

        ip_asn = get_ip_asn(ip)
        ip_target_asn = get_ip_asn(ip_target)

        if not ip_asn or not ip_target_asn:
            return False

        return ip_asn == ip_target_asn
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

        # hutils.flask.flash(_("domain.reality.asn_issue") +
        #                    f"<br> Server ASN={asn_ipv4.get('autonomous_system_organization','unknown')}<br>{domain}_ASN={asn_dip.get('autonomous_system_organization','unknown')}", "warning")


@ cache.cache(600)
def get_ip_asn(ip: ipaddress.IPv4Address | ipaddress.IPv6Address | str) -> str:
    if not IPASN:
        return __get_ip_asn_api(ip)
    try:
        if asn := IPASN.get(str(ip)):
            return str(asn.get('autonomous_system_organization', ''))
        return ''
    except:
        return ''


def __get_ip_asn_api(ip: ipaddress.IPv4Address | ipaddress.IPv6Address | str) -> str:
    ip = str(ip)
    if not is_ip(ip):
        return ''
    endpoint = f'https://ipapi.co/{ip}/asn/'
    return str(requests.get(endpoint).content)


@ cache.cache(3600)
def is_ip(input: str):
    try:
        _ = ipaddress.ip_address(input)
        return True
    except:
        return False


def resolve_domain_with_api(domain: str) -> str:
    if not domain:
        return ''
    endpoint = f'http://ip-api.com/json/{domain}?fields=query'
    return str(requests.get(endpoint).json().get('query'))
