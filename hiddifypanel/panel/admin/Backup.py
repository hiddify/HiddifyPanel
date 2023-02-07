#!/usr/bin/env python3
from hiddifypanel.panel.database import db
import uuid
from flask_babelex import gettext as _
from flask_bootstrap import SwitchField
# from flask_babelex import gettext as _
import wtforms as wtf
from flask_wtf import FlaskForm
import pathlib
from hiddifypanel.models import BoolConfig,StrConfig,ConfigEnum,hconfig,Proxy,User,Domain,DomainType

from datetime import datetime,timedelta,date
import os,sys
import json
import urllib.request
import subprocess
import re
from hiddifypanel.panel import hiddify
from flask import current_app,render_template,request,Response,Markup,url_for
from hiddifypanel.panel.hiddify import flash
from flask_wtf.file import FileField, FileRequired
import json

from flask_classful import FlaskView

class Backup(FlaskView):

    def index(self):
        return render_template('backup.html',restore_form=get_restore_form())
    
    def post(self):
        restore_form=get_restore_form()
        
        if restore_form.validate_on_submit():
            file=restore_form.restore_file.data
            json_data=json.load(file)
            new_rows=[]
            if restore_form.enable_user_restore.data:
                for user in json_data['users']:
                    print(user)
                    dbuser=User.query.filter(User.uuid==user['uuid']).first()
                    
                    if not dbuser:
                        dbuser=User()
                        dbuser.uuid=user['uuid']
                        new_rows.append(dbuser)
                    
                    dbuser.current_usage_GB=user['current_usage_GB']
                    dbuser.expiry_time=datetime.strptime(user['expiry_time'],'%Y-%m-%d')
                    dbuser.last_reset_time=datetime.strptime(user['last_reset_time'],'%Y-%m-%d')
                    dbuser.usage_limit_GB=user['usage_limit_GB']
                    dbuser.name=user['name']

                    
                        
                    
            
            if restore_form.enable_domain_restore.data:
                for domain in json_data['domains']:
                    dbdomain=Domain.query.filter(Domain.domain==domain['domain']).first()
                    if not dbdomain:
                        dbdomain=Domain(domain=domain['domain'])
                        new_rows.append(dbdomain)
                    
                    dbdomain.mode=domain['mode']

            for c,v in json_data["hconfigs"].items():
                ckey=ConfigEnum(c)
                if ckey==ConfigEnum.db_version:continue
                if ckey.type()==bool:
                    BoolConfig.query.filter(BoolConfig.key==ckey).update({'value':v})
                else:
                    StrConfig.query.filter(StrConfig.key==ckey).update({'value':v})
            
            for proxy in json_data["proxies"]:
                dbproxy=Proxy.query.filter(Proxy.name==proxy['name']).first()
                if not dbproxy:
                    dbproxy=Proxy()
                    new_rows.append(dbproxy)
                dbproxy.enable=proxy['enable']
                dbproxy.proto=proxy['proto']
                dbproxy.transport=proxy['transport']
                dbproxy.cdn=proxy['cdn']
                dbproxy.l3=proxy['l3']
            db.session.bulk_save_objects(new_rows)
            db.session.commit()
            from flask_babel import refresh; refresh()
            hiddify.flash_config_success(full_install=True)
        else:
            flash(_('Config file is incorrect'))
        return render_template('backup.html',restore_form=restore_form)
    

def get_restore_form(empty=False):
        class RestoreForm(FlaskForm):
                restore_file=FileField(_("Restore File"),description=_("Restore File Description"),validators=[FileRequired()])
                enable_user_restore=SwitchField(_("Restore Users"),description=_("Restore Users description"),default=False)
                enable_domain_restore=SwitchField(_("Restore Domain"),description=_("Restore Domain description"),default=False)
                submit=wtf.fields.SubmitField(_('Submit'))

                
        
        return RestoreForm(None) if empty else RestoreForm()