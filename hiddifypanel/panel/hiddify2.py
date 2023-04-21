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






def date_to_json(d):
    return d.strftime("%Y-%m-%d") if d else None
def json_to_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return None
def time_to_json(d):
    return d.strftime("%Y-%m-%d %H:%M:%S") if d else None    
def json_to_time(time_str):
    try:
        return datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except:
        return None


def dump_db_to_dict():
    return {"users": [u.to_dict() for u in User.query.all()],
            "domains": [u.to_dict() for u in Domain.query.all()],
            "proxies": [u.to_dict() for u in Proxy.query.all()],
            "parent_domains": [] if not hconfig(ConfigEnum.license) else [u.to_dict() for u in ParentDomain.query.all()],
            'admin_users':[d.to_dict() for d in AdminUser.query.all()],
            "hconfigs": [*[u.to_dict() for u in BoolConfig.query.all()],
                         *[u.to_dict() for u in StrConfig.query.all()]]
            }

   
def set_db_from_json(json_data, override_child_id=None, set_users=True, set_domains=True, set_proxies=True, set_settings=True, remove_domains=False, remove_users=False, override_unique_id=True,set_admins=True):
    new_rows = []
    if set_users and 'users' in json_data:
        bulk_register_users(json_data['users'],commit=False,remove=remove_users)
    if set_admins and 'admin_users' in json_data:
        bulk_register_admins(json_data['admin_users'],commit=False)
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





from .hiddify3 import *
from .hiddify import *