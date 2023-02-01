from hiddifypanel.models import BoolConfig,StrConfig,ConfigEnum,hconfig,Proxy
# from flask_babelex import lazy_gettext as __
from flask_babelex import gettext as _
import wtforms as wtf
from flask_wtf import FlaskForm, CSRFProtect
from flask_bootstrap import SwitchField

from flask_admin.base import expose
# from gettext import gettext as _


import re
from flask import render_template,current_app,flash, Markup,url_for
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,get_hconfigs
from hiddifypanel.panel.database import db
from wtforms.fields import *


# @expose("/")
def index():

    return render_template('proxy.html',global_config_form=get_global_config_form(), detailed_config_form=get_all_proxy_form() )

def get_global_config_form(empty=False):
    boolconfigs=BoolConfig.query.all()

    class DynamicForm(FlaskForm):pass

    for cf in boolconfigs:
        if cf.category=='hidden':continue
        if not cf.key.endswith("_enable"):continue
        field= SwitchField(_(f'config.{cf.key}.label'), default=cf.value,description=_(f'config.{cf.key}.description')) 
        setattr(DynamicForm, cf.key,  field)
    setattr(DynamicForm,"submit_global",wtf.fields.SubmitField(_('Submit')))
    if empty:
        return DynamicForm(None)
    return DynamicForm()

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

def get_all_proxy_form(empty=False):
    proxies=get_available_proxies()
    categories1=sorted([ c for c in {c.cdn:1 for c in proxies}])
    class DynamicForm(FlaskForm):pass

    for cdn in categories1:
        class CDNForm(FlaskForm):pass
        cdn_proxies=[c for c in proxies if c.cdn==cdn]
        protos=sorted([ c for c in {c.proto:1 for c in cdn_proxies}])
        for proto in protos:
            class ProtoForm(FlaskForm):pass
            proto_proxies=[c for c in cdn_proxies if c.proto==proto]
            for proxy in proto_proxies:
                field= SwitchField(proxy.name, default=proxy.enable,description=f"l3:{proxy.l3} transport:{proxy.transport}") 
                setattr(ProtoForm, f"p_{proxy.id}",  field)

            multifield=wtf.fields.FormField(ProtoForm,proto)
            setattr(CDNForm, proto,  multifield)
        multifield=wtf.fields.FormField(CDNForm,cdn)
        setattr(DynamicForm, cdn,  multifield)
    setattr(DynamicForm,"submit_detail",wtf.fields.SubmitField(_('Submit')))
    if empty:
        return DynamicForm(None)
    return DynamicForm()


def save():
    global_config_form=get_global_config_form()
    all_proxy_form=get_all_proxy_form()

    if global_config_form.submit_global.data and global_config_form.validate_on_submit():
            
            for k,vs in global_config_form.data.items():
                    if k in [c for c in ConfigEnum]:
                        BoolConfig.query.filter(BoolConfig.key==k).first().value=vs
                        if vs and k in [ConfigEnum.domain_fronting_http_enable, ConfigEnum.domain_fronting_tls_enable]:
                            flash(Markup(_('config.domain-fronting-notsetup-error')), 'danger')                

                
            # print(cat,vs)
            db.session.commit()
            apply_btn=f"<a href='{url_for('admin.actions.apply_configs')}' class='btn btn-primary'>"+_("admin.config.apply_configs")+"</a>"
            flash(Markup(_('config.validation-success',link=apply_btn)), 'success')
            all_proxy_form=get_all_proxy_form(True)

   
    elif all_proxy_form.submit_detail.data and all_proxy_form.validate_on_submit():
        
        for cdn,vs in all_proxy_form.data.items():#[c for c in ConfigEnum]:
            if type(vs) is not dict:continue
            for proto,v in vs.items():#[c for c in ConfigEnum]:
                if type(v) is not dict:continue
                for proxy_id,enable in v.items():
                    if not proxy_id.startswith("p_"):continue
                    id=int(proxy_id.split('_')[-1])
                    Proxy.query.filter(Proxy.id==id).first().enable=enable
                        
                    
            # print(cat,vs)
        db.session.commit()
        apply_btn=f"<a href='{url_for('admin.actions.apply_configs')}' class='btn btn-primary'>"+_("admin.config.apply_configs")+"</a>"
        flash(Markup(_('config.validation-success',link=apply_btn)), 'success')
        global_config_form= get_global_config_form(True)
    else:
        flash(Markup(_('config.validation-error')), 'danger')

    return render_template('proxy.html', global_config_form=global_config_form, detailed_config_form=all_proxy_form)
    

    
    import flask_babelex
    

    # form=HelloForm()
    # # return render('config.html',form=form)
    # return render_template('config.html',form=HelloForm())
    form=get_config_form()
    return render_template('config.html',form=form)

