from flask import g,jsonify
from hiddifypanel.models import User,Domain,BoolConfig,StrConfig,hconfig,ConfigEnum
import uuid
from flask import g,send_from_directory,url_for

def init_app(app):    
    app.jinja_env.globals['ConfigEnum'] = ConfigEnum
    app.jinja_env.globals['hconfig'] = hconfig

    

    @app.url_defaults
    def add_proxy_path_user(endpoint, values):
        if 'user_secret' not in values:
            values['user_secret']=f'{g.user_uuid}'
        if 'proxy_path' not in values:
            values['proxy_path']=f'{g.proxy_path}'
    
    @app.url_value_preprocessor
    def pull_secret_code(endpoint, values):
        print("Y",endpoint, values)
        g.user=None
        g.user_uuid = None
        g.is_admin = False

        g.proxy_path =  values.pop('proxy_path', None) if values else None
        tmp_secret=values.pop('user_secret', None) if values else None
        try:
            if tmp_secret:
                g.user_uuid =  uuid.UUID(tmp_secret)
        except:
            raise Exception("Invalid secret")
        g.is_admin = f'{g.user_uuid}'==hconfig(ConfigEnum.admin_secret)
        
        if not g.is_admin:
            g.user=User.query.filter(User.uuid==f'{g.user_uuid}').first()

        