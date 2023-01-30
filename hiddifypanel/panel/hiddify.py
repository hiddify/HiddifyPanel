from flask import jsonify,g
to_gig_d = 1024*1024*1024
import datetime
from hiddifypanel.panel.database import db
from hiddifypanel.models import StrConfig,BoolConfig,User,Domain,get_hconfigs
import urllib
def auth(function):
    def wrapper(*args,**kwargs):
        if g.user_uuid==None:
            return jsonify({"error":"auth failed"})
        if not admin and g.is_admin:
            return jsonify({"error":"admin can not access user page. add /admin/ to your url"})
    
        return function()

    return wrapper
def admin(function):
    def wrapper(*args,**kwargs):
        if g.user_uuid==None:
            return jsonify({"error":"auth failed"})
        if not g.is_admin:
            return jsonify({"error":"invalid admin"})
    
        return function()

    return wrapper

def abs_url(path):
    return f"/{g.proxy_path}/{g.user_uuid}/{path}"
def asset_url(path):
    return f"/{g.proxy_path}/{path}"
def update_usage():
        
        res={}
        for user in db.session.query(User).all():
            if (datetime.today()-last_rest_time).days>=30:
                user.last_rest_time=datetime.today()
                if user.current_usage_GB > user.monthly_usage_limit_GB:
                    xray_api.add_client(user.uuid)
                user.current_usage_GB=0

            d = xray_api.get_usage(user.uuid)
            
            if d == None:
               res[user.uuid]="No value" 
            else:
                in_gig=(d)/to_gig_d
                res[user.uuid]=in_gig
                user.current_usage_GB += in_gig
            if user.current_usage_GB > user.monthly_usage_limit_GB:
                xray_api.remove_client(user.uuid)
                res[user.uuid]+=" !OUT of USAGE! Client Removed"
                    
        db.session.commit()
        
        return {"status": 'success', "comments":res}
        


def all_configs():
    return {
        "users": [u.to_dict() for u in User.query.filter((User.monthly_usage_limit_GB>User.current_usage_GB)).filter(User.expiry_time>=datetime.date.today()).all()],
        "domains": [u.to_dict() for u in Domain.query.all()],
        "hconfigs": get_hconfigs()
        }
    

def get_ip(version,retry=3):
    try:
        return urllib.request.urlopen(f'https://v{version}.ident.me/').read().decode('utf8')
    except:
        if retry==0:
            return None
        return get_ip(version,retry=retry-1)
