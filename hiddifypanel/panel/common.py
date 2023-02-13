from flask import g,jsonify,abort,render_template,request
from hiddifypanel.models import User,Domain,BoolConfig,StrConfig,hconfig,ConfigEnum
from hiddifypanel.panel import hiddify
import uuid
from flask import g,send_from_directory,url_for
import traceback
def init_app(app):    
    app.jinja_env.globals['ConfigEnum'] = ConfigEnum
    app.jinja_env.globals['hconfig'] = hconfig
    
    

    @app.errorhandler(Exception)
    def internal_server_error(e):
        if not hasattr(e,'code') or e.code==500:
            trace=traceback.format_exc()
            return render_template('500.html',error=e,trace=trace), 500
        # if e.code in [400,401,403]:
        #     return render_template('access-denied.html',error=e), e.code     
        
        return render_template('error.html',error=e), e.code


    @app.url_defaults
    def add_proxy_path_user(endpoint, values):

        if 'user_secret' not in values and hasattr(g,'user_uuid'):
            values['user_secret']=f'{g.user_uuid}'
        if 'proxy_path' not in values:
            # values['proxy_path']=f'{g.proxy_path}'
            values['proxy_path']=hconfig(ConfigEnum.proxy_path)

        
    
    @app.url_value_preprocessor
    def pull_secret_code(endpoint, values):
        # print("Y",endpoint, values)
        # if values is None:
        #     return 
        
        g.user=None
        g.user_uuid = None
        g.is_admin = False

        g.proxy_path =  values.pop('proxy_path', None) if values else None
        if g.proxy_path!=hconfig(ConfigEnum.proxy_path):
            abort(400,"Invalid Proxy Path")
        if endpoint=='static':
            return
        tmp_secret=values.pop('user_secret', None) if values else None
        try:
            if tmp_secret:
                g.user_uuid =  uuid.UUID(tmp_secret)
        except:
            # raise PermissionError("Invalid secret")
            abort(400,'invalid user')
        g.is_admin = f'{g.user_uuid}'==hconfig(ConfigEnum.admin_secret)
        
        if not g.is_admin:
            g.user=User.query.filter(User.uuid==f'{g.user_uuid}').first()
            if not g.user:
                abort(401,'invalid user')
            if endpoint and ("admin" in endpoint or "api" in endpoint) :
                # raise PermissionError("Access Denied")
                abort(403,'Access Denied')


        # print(g.user)