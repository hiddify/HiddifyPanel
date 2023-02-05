from flask import abort, render_template,request,Response,g
from wtforms.validators import Regexp,ValidationError
import urllib,uuid
import datetime
from hiddifypanel.models import User,Domain,BoolConfig,StrConfig,DomainType,ConfigEnum,get_hconfigs,get_hdomains
from hiddifypanel.panel.hiddify  import auth
from . import link_maker
from flask_classful import FlaskView,route
import random
from urllib.parse import urlparse
class UserView(FlaskView):

    def index(self):
        
        c=get_common_data(g.user_uuid)
        return render_template('home/index.html',**c)
        

    @route('/clash/<meta_or_normal>/proxies.yml')
    @route('/clash/proxies.yml')
    def clash_proxies(self,meta_or_normal="normal"):
        c=get_common_data(g.user_uuid)
        resp= Response(render_template('clash_proxies.yml',meta_or_normal=meta_or_normal,**c))
        resp.mimetype="text/plain"
        
        return resp
    
    @route('/clash/<mode>.yml')
    @route('/clash/<meta_or_normal>/<mode>.yml')
    def clash_config(self,meta_or_normal="normal",mode="all.yml"):
        
        
        c=get_common_data(g.user_uuid)
        
        
        hash_rnd=random.randint(0,1000000) #hash(f'{c}')
        resp= Response(render_template('clash_config.yml',mode=mode,meta_or_normal=meta_or_normal,**c,hash=hash_rnd))
        resp.mimetype="text/plain"
        resp.headers['Subscription-Userinfo']=f"upload=0;download={c['usage_current_b']};total={c['usage_limit_b']};expire={c['expire_s']}"
        return resp

    @route('/all.txt')
    def all_configs(self):
        c=get_common_data(g.user_uuid)
        # response.content_type = 'text/plain';
        
        resp= render_template('all_configs.txt',**c,base64=do_base_64)
        res=""
        for line in resp.split("\n"):
            if "vmess://" in line:
                line="vmess://"+do_base_64(line.replace("vmess://",""))
            res+=line+"\n"
        return Response(res,mimetype="text/plain")

def do_base_64(str):
    import base64
    resp=base64.b64encode(f'{str}'.encode("utf-8"))
    return resp.decode()
    
def get_common_data(user_uuid):
    
    
    o = urlparse(request.base_url)
    db_domain=Domain.query.filter(Domain.domain==o.hostname).first()
    domain=o.hostname
    direct_host= domain
    is_cdn=False
    if db_domain and db_domain.mode==DomainType.cdn:
        direct_host=urllib.request.urlopen('https://v4.ident.me/').read().decode('utf8')
        is_cdn=True
    
    
    # uuid_secret=str(uuid.UUID(user_secret))
    user=User.query.filter(User.uuid==f'{user_uuid}').first()
    if user is None:
        abort(401,"Invalid User")
    g.domain=domain
    g.direct_host=direct_host
    g.is_cdn=is_cdn
    return {
        'direct_host':direct_host,
        'user':user,
        'domain':domain,
        'is_cdn':is_cdn,
        'usage_limit_b':int(user.usage_limit_GB*1024*1024*1024),
        'usage_current_b':int(user.current_usage_GB*1024*1024*1024),
        'expire_s':int((user.expiry_time-datetime.date(1970, 1, 1)).total_seconds()),
        'expire_days':(user.expiry_time-datetime.date.today()).days,
        'reset_day':30-(datetime.date.today()-user.last_reset_time).days,
        'hconfigs':get_hconfigs(),
        'hdomains':get_hdomains(),
        'ConfigEnum':ConfigEnum,
        'link_maker':link_maker
    }
    