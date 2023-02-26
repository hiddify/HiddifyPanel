from flask import jsonify,g,url_for,Markup
from flask import flash as flask_flash
to_gig_d = 1000*1000*1000
import datetime

from hiddifypanel.panel.database import db
from hiddifypanel.panel import hiddify,hiddify_api
from hiddifypanel.models import *
import urllib
from flask_babelex import lazy_gettext as _
from flask_babelex import gettext as __
from hiddifypanel import xray_api
from sqlalchemy.orm import Load 

package_mode_dic={
        UserMode.daily:1,
        UserMode.weekly:7,
        UserMode.monthly:30

    }

def update_local_usage():
        
        res={}
        have_change=False
        for user in User.query.all():
            d = xray_api.get_usage(user.uuid,reset=True)
            res[user]=d

        return add_users_usage(res)
            
        # return {"status": 'success', "comments":res}
        

def add_users_usage_uuid(uuids_bytes):
    users= User.query.filter(User.uuid.in_(keys(uuids)))
    dbusers_bytes={u:uuids_bytes.get(u.uuid,0) for u in users}
    add_users_usage(dbusers_bytes)

    
def add_users_usage(dbusers_bytes):
    if not hconfig(ConfigEnum.is_parent) and hconfig(ConfigEnum.parent_panel):
        return hiddify_api.add_user_usage_to_parent(dbusers_bytes);
    res={}
    have_change=False
    for user,usage_bytes in dbusers_bytes.items():
        if user.mode!=UserMode.no_reset and (datetime.date.today()-user.last_reset_time).days>=package_mode_dic.get(user.mode,1000):
            user.last_reset_time=datetime.date.today()
            if user.current_usage_GB > user.usage_limit_GB:
                xray_api.add_client(user.uuid)
                have_change=True
            user.current_usage_GB=0

        if usage_bytes == None:
            res[user.uuid]="No value" 
        else:
            in_gig=(usage_bytes)/to_gig_d
            res[user.uuid]=in_gig
            user.current_usage_GB += in_gig
            user.last_online=datetime.datetime.now()

        if user.current_usage_GB > user.usage_limit_GB:
            xray_api.remove_client(user.uuid)
            have_change=True
            res[user.uuid]+=" !OUT of USAGE! Client Removed"
    db.session.commit()
    if have_change:
        hiddify.quick_apply_users()

    return {"status": 'success', "comments":res}



