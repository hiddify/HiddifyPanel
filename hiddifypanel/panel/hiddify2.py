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
to_gig_d = 1000*1000*1000

from .hiddify3 import *
from .hiddify import *

def format_timedelta(delta, add_direction=True,granularity="days"):
    res=delta.days
    print(delta.days)
    locale=g.locale if g and hasattr(g, "locale") else hconfig(ConfigEnum.admin_lang)
    if granularity=="days" and delta.days==0:
        res= _("0 - Last day")
    elif delta.days < 7 or delta.days >= 60:
        res= babel_format_timedelta(delta, threshold=1, add_direction=add_direction, locale=locale)
    elif delta.days < 60:
        res= babel_format_timedelta(delta, granularity="day", threshold=10, add_direction=add_direction, locale=locale)
    return res












def get_child(unique_id):
    child_id=0  
    if unique_id is None:
        child_id= 0
    else:
        child = Child.query.filter(Child.unique_id == str(unique_id)).first()
        if not child:
            child=Child(unique_id=str(unique_id))
            db.session.add(child)
            db.session.commit()
            child = Child.query.filter(Child.unique_id == str(unique_id)).first()
        child_id= child.id
    return child_id



def domain_dict(d):
    return {
        'domain': d.domain,
        'mode': d.mode,
        'alias': d.alias,
        'child_unique_id': d.child.unique_id if d.child else '',
        'cdn_ip': d.cdn_ip,
        'show_domains': [dd.domain for dd in d.show_domains]
    }


def parent_domain_dict(d):
    return {
        'domain': d.domain,
        'show_domains': [dd.domain for dd in d.show_domains]
    }

def date_to_json(d):
    return d.strftime("%Y-%m-%d") if d else None

def user_dict(d):
    return {
        'uuid':d.uuid,
        'name':d.name,
        'last_online':str(d.last_online),
        'usage_limit_GB':d.usage_limit_GB,
        'package_days':d.package_days,
        'mode':d.mode,
        'start_date':date_to_json(d.start_date),
        'current_usage_GB':d.current_usage_GB,
        'last_reset_time':date_to_json(d.last_reset_time),
        'comment':d.comment
    }


def proxy_dict(d):
    return {
        'name': d.name,
        'enable': d.enable,
        'proto': d.proto,
        'l3': d.l3,
        'transport': d.transport,
        'cdn': d.cdn,
        'child_unique_id': d.child.unique_id if d.child else ''
    }

def config_dict(d):
    return {
        'key': d.key,
        'value': d.value,
        'child_unique_id': d.child.unique_id if d.child else ''
    }


def dump_db_to_dict():
    return {"users": [user_dict(u) for u in User.query.all()],
            "domains": [domain_dict(u) for u in Domain.query.all()],
            "proxies": [proxy_dict(u) for u in Proxy.query.all()],
            "parent_domains": [] if not hconfig(ConfigEnum.license) else [parent_domain_dict(u) for u in ParentDomain.query.all()],
            "hconfigs": [*[config_dict(u) for u in BoolConfig.query.all()],
                         *[config_dict(u) for u in StrConfig.query.all()]]
            }
def add_or_update_parent_domains(commit=True,**parent_domain):
    dbdomain = ParentDomain.query.filter(
         ParentDomain.domain == parent_domain['domain']).first()
    if not dbdomain:
        dbdomain = ParentDomain(domain=parent_domain['domain'])
        db.session.add(dbdomain)
    show_domains = parent_domain.get('show_domains', [])
    dbdomain.show_domains = Domain.query.filter(
        Domain.domain.in_(show_domains)).all()
    if commit:
        db.session.commit()

def add_or_update_proxy(commit=True,child_id=0,**proxy):
    dbproxy = Proxy.query.filter(
        Proxy.name == proxy['name']).first()
    if not dbproxy:
        dbproxy = Proxy()
        db.session.add(dbproxy)
    dbproxy.enable = proxy['enable']
    dbproxy.name = proxy['name']
    dbproxy.proto = proxy['proto']
    dbproxy.transport = proxy['transport']
    dbproxy.cdn = proxy['cdn']
    dbproxy.l3 = proxy['l3']
    dbproxy.child_id = child_id
    if commit:
        db.session.commit()
def add_or_update_domain(commit=True,child_id=0,**domain):
    dbdomain = Domain.query.filter(
        Domain.domain == domain['domain']).first()
    if not dbdomain:
        dbdomain = Domain(domain=domain['domain'])
        db.session.add(dbdomain)
    dbdomain.child_id = child_id

    dbdomain.mode = domain['mode']
    dbdomain.cdn_ip = domain.get('cdn_ip', '')
    dbdomain.alias = domain.get('alias', '')
    show_domains = domain.get('show_domains', [])
    dbdomain.show_domains = Domain.query.filter(
        Domain.domain.in_(show_domains)).all()
    if commit:
        db.session.commit()

def add_or_update_user1(commit=True,**user):
    dbuser = User.query.filter(User.uuid == user['uuid']).first()

    if not dbuser:
        dbuser = User()
        dbuser.uuid = user['uuid']
        db.session.add(dbuser)
    
    if user.get('expiry_time',''):
        if user.get('last_reset_time',''):
            last_reset_time = datetime.datetime.strptime(user['last_reset_time'], '%Y-%m-%d')
        else:
            last_reset_time = datetime.date.today()

        expiry_time = datetime.datetime.strptime(user['expiry_time'], '%Y-%m-%d')
        dbuser.start_date=    last_reset_time
        dbuser.package_days=(expiry_time-last_reset_time).days

    elif 'package_days' in user:
        dbuser.package_days=user['package_days']
        if user.get('start_date',''):
            dbuser.start_date=datetime.datetime.strptime(user['start_date'], '%Y-%m-%d')
        else:
            dbuser.start_date=None
    dbuser.current_usage_GB = user['current_usage_GB']
    
    dbuser.usage_limit_GB = user['usage_limit_GB']
    dbuser.name = user['name']
    dbuser.comment = user.get('comment', '')
    dbuser.mode = user.get('mode', user.get('monthly', 'false') == 'true')
    # dbuser.last_online=user.get('last_online','')
    if commit:
        db.session.commit()


def bulk_register_parent_domains(parent_domains,commit=True,remove=False):
    for p in parent_domains:
        add_or_update_parent_domains(commit=False,**p)
    if remove:
        dd = {p.domain: 1 for p in parent_domains}
        for d in ParentDomain.query.all():
            if d.domain not in dd:
                db.session.delete(d)
    if commit:
        db.session.commit()

def bulk_register_domains(domains,commit=True,remove=False,override_child_id=None):
    child_ids={}
    for domain in domains:
        child_id=override_child_id if override_child_id is not None else get_child(domain.get('child_unique_id',None))
        child_ids[child_id]=1
        add_or_update_domain(commit=False,child_id=child_id,**domain)
    if remove and len(child_ids):
        dd = {d['domain']: 1 for d in domains}
        for d in Domain.query.filter(Domain.child_id.in_(child_ids)):
            if d.domain not in dd:
                db.session.delete(d)
    if commit:
        db.session.commit()
def bulk_register_users(users=[],commit=True,remove=False):
    for u in users:
        add_or_update_user(commit=False,**u)
    if remove:
        dd = {u.uuid: 1 for u in users}
        for d in User.query.all():
            if d.uuid not in dd:
                db.session.delete(d)
    if commit:
        db.session.commit()
def bulk_register_configs(hconfigs,commit=True,override_child_id=None,override_unique_id=True):
    print(hconfigs)
    for conf in hconfigs:
        # print(conf)
        if conf['key']==ConfigEnum.unique_id and not override_unique_id:
            continue
        child_id=override_child_id if override_child_id is not None else get_child(conf.get('child_unique_id',None))
        # print(conf)
        add_or_update_config(commit=False,child_id=child_id,**conf)
    if commit:
        db.session.commit()

def bulk_register_proxies(proxies,commit=True,override_child_id=None):
    for proxy in proxies:
        child_id=override_child_id if override_child_id is not None else get_child(proxy.get('child_unique_id',None))
        add_or_update_proxy(commit=False,child_id=child_id,**proxy)

    
def set_db_from_json(json_data, override_child_id=None, set_users=True, set_domains=True, set_proxies=True, set_settings=True, remove_domains=False, remove_users=False, override_unique_id=True):
    new_rows = []
    if set_users and 'users' in json_data:
        bulk_register_users(json_data['users'],commit=False,remove=remove_users)
    if set_domains and 'domains' in json_data:
        bulk_register_domains(json_data['domains'],commit=False,remove=remove_domains,override_child_id=override_child_id)
    if set_domains and 'parent_domains' in json_data:
        bulk_register_parent_domains(json_data['parent_domains'],commit=False,remove=remove_domains)
    if set_settings and 'hconfigs' in json_data:
        bulk_register_configs(json_data["hconfigs"],commit=False,override_child_id=override_child_id,override_unique_id=override_unique_id)
        if 'proxies' in json_data:
            bulk_register_proxies(json_data['proxies'],commit=False,override_child_id=override_child_id)
    db.session.commit()




def get_random_string(min_=10,max_=30):
    # With combination of lower and upper case
    import string
    import random
    length=random.randint(min_, max_)
    characters = string.ascii_letters + string.digits
    result_str = ''.join(random.choice(characters) for i in range(length))
    return result_str




