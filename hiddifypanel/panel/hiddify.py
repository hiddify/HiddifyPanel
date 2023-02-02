from flask import jsonify,g,flash,url_for
to_gig_d = 1024*1024*1024
import datetime
from hiddifypanel.panel.database import db
from hiddifypanel.models import StrConfig,BoolConfig,User,Domain,get_hconfigs,Proxy,hconfig,ConfigEnum
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


def get_available_proxies():
    proxies=Proxy.query.all()
    
    if not hconfig(ConfigEnum.domain_fronting_domain):
        proxies=[c for c in proxies if 'Fake' not in c.cdn]
    if not hconfig(ConfigEnum.ssfaketls_enable):
        proxies=[c for c in proxies if 'faketls' != c.transport]
        proxies=[c for c in proxies if 'v2ray' != c.proto]
    if not hconfig(ConfigEnum.shadowtls_enable):
        proxies=[c for c in proxies if c.transport!='shadowtls']
    if not hconfig(ConfigEnum.ssr_enable):
        proxies=[c for c in proxies if 'ssr' != c.proto]
    if not hconfig(ConfigEnum.vmess_enable):
        proxies=[c for c in proxies if 'vmess' not in c.proto]

    if not hconfig(ConfigEnum.kcp_enable):
        proxies=[c for c in proxies if 'kcp' not in c.l3]
    
    if not hconfig(ConfigEnum.http_proxy_enable):
        proxies=[c for c in proxies if 'http' != c.l3]
    return proxies


def flash_config_success():
    apply_btn=f"<a href='{url_for('admin.Actions:apply_configs')}' class='btn btn-primary'>"+_("admin.config.apply_configs")+"</a>"
    flash(Markup(_('config.validation-success',link=apply_btn)), 'success')