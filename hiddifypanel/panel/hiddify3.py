import socket
from sqlalchemy.orm import Load
from babel.dates import format_timedelta as babel_format_timedelta

from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _
import urllib
from hiddifypanel.models import *
from hiddifypanel.panel.database import db
import datetime
from flask import jsonify, g, url_for, Markup,abort
from wtforms.validators import ValidationError
from flask import flash as flask_flash
import random
import string
to_gig_d = 1000*1000*1000



import psutil
import time
import os
from .hiddify2 import *
from .hiddify import *
def system_stats():
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # RAM usage
    ram_stats = psutil.virtual_memory()
    ram_used = ram_stats.used/ 1024**3
    ram_total = ram_stats.total/ 1024**3
    
    # Disk usage (in GB)
    disk_stats = psutil.disk_usage('/')
    disk_used = disk_stats.used / 1024**3
    disk_total = disk_stats.total / 1024**3

    hiddify_used = get_folder_size('/opt/hiddify-config/')/ 1024**3
    

    # Network usage
    net_stats = psutil.net_io_counters()
    bytes_sent_cumulative = net_stats.bytes_sent 
    bytes_recv_cumulative = net_stats.bytes_recv 
    bytes_sent = net_stats.bytes_sent - getattr(system_stats, 'prev_bytes_sent', 0)
    bytes_recv = net_stats.bytes_recv - getattr(system_stats, 'prev_bytes_recv', 0)
    system_stats.prev_bytes_sent = net_stats.bytes_sent
    system_stats.prev_bytes_recv = net_stats.bytes_recv
    
    # Total connections and unique IPs
    connections = psutil.net_connections()
    total_connections = len(connections)
    unique_ips = set([conn.raddr.ip for conn in connections if conn.status == 'ESTABLISHED' and conn.raddr])
    total_unique_ips = len(unique_ips)
    
    # Load average
    num_cpus = psutil.cpu_count()
    load_avg = [avg / num_cpus for avg in os.getloadavg()]
    # Return the system information
    return {
        "cpu_percent": cpu_percent,
        "ram_used": ram_used,
        "ram_total": ram_total,
        "disk_used": disk_used,
        "disk_total": disk_total,
        "hiddify_used":hiddify_used,
        "bytes_sent": bytes_sent,
        "bytes_recv": bytes_recv,
        "bytes_sent_cumulative":bytes_sent_cumulative,
        "bytes_recv_cumulative":bytes_recv_cumulative,
        "net_sent_cumulative_GB":bytes_sent_cumulative/ 1024**3,
        "net_total_cumulative_GB":(bytes_sent_cumulative+bytes_recv_cumulative)/ 1024**3,
        "total_connections": total_connections,
        "total_unique_ips": total_unique_ips,
        "load_avg_1min": load_avg[0],
        "load_avg_5min": load_avg[1],
        "load_avg_15min": load_avg[2],
    }


import psutil


def top_processes():
    # Get the process information
    processes = [p for p in psutil.process_iter(['name', 'memory_full_info', 'cpu_percent']) if p.info['name'] != '']
    num_cores = psutil.cpu_count()
    # Calculate memory usage, RAM usage, and CPU usage for each process
    memory_usage = {}
    ram_usage = {}
    cpu_usage = {}
    for p in processes:
        name = p.info['name']
        if "python3" in name or "uwsgi" in name or 'flask' in name:
            name="Hiddify"
        mem_info = p.info['memory_full_info']
        if mem_info is None:
            continue
        mem_usage = mem_info.uss
        cpu_percent = p.info['cpu_percent']/num_cores
        if name in memory_usage:
            memory_usage[name] += mem_usage / (1024 ** 3)
            ram_usage[name] += mem_info.rss / (1024 ** 3)
            cpu_usage[name] += cpu_percent
        else:
            memory_usage[name] = mem_usage / (1024 ** 3)
            ram_usage[name] = mem_info.rss / (1024 ** 3)
            cpu_usage[name] = cpu_percent
    
    # Sort the processes by memory usage, RAM usage, and CPU usage
    top_memory = sorted(memory_usage.items(), key=lambda x: x[1], reverse=True)[:5]
    top_ram = sorted(ram_usage.items(), key=lambda x: x[1], reverse=True)[:5]
    top_cpu = sorted(cpu_usage.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Return the top processes for memory usage, RAM usage, and CPU usage
    return {
        "memory": top_memory,
        "ram": top_ram,
        "cpu": top_cpu
    }


def get_folder_size(folder_path):
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for file in filenames:
                file_path = os.path.join(dirpath, file)
                try:
                    total_size += os.path.getsize(file_path)
                except:
                    pass
    except:
        pass
    return total_size

def get_domain_btn_link(domain):
        text = domain.alias or domain.domain
        color_cls="info"
        if domain.mode in [DomainType.cdn,DomainType.auto_cdn_ip]:
            auto_cdn=(domain.mode==DomainType.auto_cdn_ip) or (domain.cdn_ip and "MTN" in domain.cdn_ip)
            color_cls="success" if auto_cdn else 'warning'
            text = f'<span class="badge badge-secondary" >{"Auto" if auto_cdn else "CDN"}</span> '+text
        res = f"<a target='_blank' href='#' class='btn btn-xs btn-{color_cls} ltr' ><i class='fa-solid fa-arrow-up-right-from-square d-none'></i> {text}</a>"
        return res


def get_random_string(min_=10,max_=30):
    # With combination of lower and upper case
    length=random.randint(min_, max_)
    characters = string.ascii_letters + string.digits
    result_str = ''.join(random.choice(characters) for i in range(length))
    return result_str

def get_random_domains(count=1,retry=3):
    try:
        irurl="https://api.ooni.io/api/v1/measurements?probe_cc=IR&test_name=web_connectivity&anomaly=false&confirmed=false&failure=false&order_by=test_start_time&limit=1000"
        # cnurl="https://api.ooni.io/api/v1/measurements?probe_cc=CN&test_name=web_connectivity&anomaly=false&confirmed=false&failure=false&order_by=test_start_time&limit=1000"
        import requests
        data_ir=requests.get(irurl).json()
        # data_cn=requests.get(url).json()
        from urllib.parse import urlparse
        domains=[urlparse(d['input']).netloc.lower() for d in data_ir['results'] if d['scores']['blocking_country']==0.0]
        domains=[d for d in domains if not d.endswith(".ir")]
        
        return random.sample(domains, count)
    except Exception as e:
        print('Error, getting random domains... ',e,'retrying...',retry)
        if retry<=0:
            defdomains=["fa.wikipedia.org",'en.wikipedia.org','wikipedia.org','yahoo.com','en.yahoo.com']
            print('Error, using default domains')
            return random.sample(defdomains, count)
        return get_random_domains(count,retry-1)


def is_domain_support_tls_13(domain):
    import ssl
    import socket

    context = ssl.create_default_context()
    with socket.create_connection((domain, port)) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            return ssock.version()=="TLSv1.3"

def is_domain_support_h2(domain):
    try:
        import h2.connection
        import socket
        import ssl
        context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        context.options |= (ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
        context.options |= ssl.OP_NO_COMPRESSION
        context.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")
        context.set_alpn_protocols(["h2"])
        with socket.create_connection((domain, port)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                return ssock.version()=="TLSv1.3"
    except:
        return False

def is_domain_reality_friendly(domain):
    return is_domain_support_h2(domain)

def generate_x25519_keys():
    # Run the "xray x25519" command and capture its output
    cmd = "xray x25519"
    import subprocess
    output = subprocess.check_output(cmd, shell=True, text=True)

    # Extract the private and public keys from the output
    private_key = output.split("Private key: ")[1].split("\n")[0]
    public_key = output.split("Public key: ")[1].split("\n")[0]

    # Return the keys as a tuple
    return {"private_key":private_key, "public_key":public_key}