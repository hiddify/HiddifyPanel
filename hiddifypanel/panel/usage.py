from flask import jsonify,g,url_for,Markup
from flask import flash as flask_flash
to_gig_d = 1000*1000*1000
import datetime

from hiddifypanel.panel.database import db
# from hiddifypanel.panel import hiddify_api #hiddify
from hiddifypanel.models import *
import urllib
from flask_babelex import lazy_gettext as _
from flask_babelex import gettext as __
from hiddifypanel import xray_api
from sqlalchemy.orm import Load 


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

def is_already_valid(uuid):
    xray_api.get_xray_client().add_client(t,f'{uuid}', f'{uuid}@hiddify.com',protocol=protocol,flow='xtls-rprx-vision',alter_id=0,cipher='chacha20_poly1305')
    
def add_users_usage(dbusers_bytes):
    if not hconfig(ConfigEnum.is_parent) and hconfig(ConfigEnum.parent_panel):
        from hiddifypanel.panel import hiddify_api
        hiddify_api.add_user_usage_to_parent(dbusers_bytes);
    res={}
    have_change=False
    before_enabled_users=xray_api.get_enabled_users()
    for user,usage_bytes in dbusers_bytes.items():
        # user_active_before=is_user_active(user)

        if not user.last_reset_time or (user.last_reset_time-datetime.date.today()).days>0:
            reset_days=days_to_reset(user)
            if reset_days==0:
                user.last_reset_time=datetime.date.today()
                user.current_usage_GB=0

        if before_enabled_users[user.uuid]==0  and is_user_active(user):
                xray_api.add_client(user.uuid)
                have_change=True

        if usage_bytes == None:
            res[user.uuid]="No value" 
        else:
            in_gig=(usage_bytes)/to_gig_d
            res[user.uuid]=in_gig
            user.current_usage_GB += in_gig
            user.last_online=datetime.datetime.now()
            if user.start_date==None:
                user.start_date=datetime.date.today()

        if before_enabled_users[user.uuid]==1 and not is_user_active(user):
            xray_api.remove_client(user.uuid)
            have_change=True
            res[user.uuid]=f"{res[user.uuid]} !OUT of USAGE! Client Removed"

    db.session.commit()
    # if have_change:
    #     hiddify.quick_apply_users()

    return {"status": 'success', "comments":res}



