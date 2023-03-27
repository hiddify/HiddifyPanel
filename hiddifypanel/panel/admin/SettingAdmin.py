import flask_babel,flask_babelex
from hiddifypanel.models import BoolConfig,StrConfig,ConfigEnum,hconfig,ConfigCategory
from wtforms.validators import Regexp, ValidationError
from flask_babelex import lazy_gettext as _
# from flask_babelex import gettext as _
import wtforms as wtf
from flask_wtf import FlaskForm, CSRFProtect
from flask_bootstrap import SwitchField

from flask_admin.base import expose
# from gettext import gettext as _


import re
from flask import render_template,current_app, Markup,url_for
from hiddifypanel.panel.hiddify import flash
from hiddifypanel.models import  *
from hiddifypanel.panel.database import db
from wtforms.fields import *
from flask_classful import FlaskView
from hiddifypanel.panel import hiddify,hiddify_api,custom_widgets

class SettingAdmin(FlaskView):
    


    def index(self):
        # return "d"
        
        

        # form=HelloForm()
        # # return render('config.html',form=form)
        # return render_template('config.html',form=HelloForm())
        form=get_config_form()
        return render_template('config.html',form=form)


    def post(self):
        form=get_config_form()
        if form.validate_on_submit():
            

            boolconfigs=BoolConfig.query.filter(BoolConfig.child_id==0).all()
            bool_types={c.key:'bool' for c in boolconfigs}
            old_configs=get_hconfigs()
            for cat,vs in form.data.items():#[c for c in ConfigEnum]:
            
                if type(vs) is dict:
                    for k,v in vs.items():
            
                        if k in [c for c in ConfigEnum if not c.commercial()]:
                            if k in bool_types:
                                BoolConfig.query.filter(BoolConfig.key==k,BoolConfig.child_id==0).first().value=v
                            else:
                                if "_domain" in k or k in [ConfigEnum.admin_secret]:
                                    v=v.lower()
                                if "port" in k:
                                    for p in v.split(","):
                                        for k2,v2 in vs.items():
                                            if "port" in k2 and k!=k2 and p in v2:
                                                flash(_("Port is already used! in")+f" {k2} {k}",'error')
                                                return render_template('config.html', form=form)    
                                StrConfig.query.filter(StrConfig.key==k,StrConfig.child_id==0).first().value=v

                # print(cat,vs)

            db.session.commit()
            flask_babel.refresh()
            flask_babelex.refresh()
            
        
            reset_action=hiddify.check_need_reset(old_configs)
            if reset_action:
                return reset_action
            
            if old_configs[ConfigEnum.admin_lang]!=hconfig(ConfigEnum.admin_lang):
                form=get_config_form()
            return render_template('config.html', form=form)
        flash(_('config.validation-error'), 'danger')
        return render_template('config.html', form=form)

        
        
        

        form=get_config_form()
        return render_template('config.html',form=form)

    def get_babel_string(self):
        res=""
        strconfigs=StrConfig.query.all()
        boolconfigs=BoolConfig.query.all()
        bool_types={c.key:'bool' for c in boolconfigs}

        configs=[*boolconfigs,*strconfigs]
        for cat in ConfigCategory:
            if cat=='hidden':continue

            cat_configs=[c for c in configs if c.key.category()==cat]
            
            for c in cat_configs:
                res+=f'{{{{_("config.{c.key}.label")}}}} {{{{_("config.{c.key}.description")}}}}'
                

            res+=f'{{{{_("config.{cat}.label")}}}}{{{{_("config.{cat}.description")}}}}'
        for c in ConfigEnum:
            res+=f'{{{{_("config.{c}.label")}}}} {{{{_("config.{c}.description")}}}}'
        return res
        

def get_config_form():
    
    
    strconfigs=StrConfig.query.filter(StrConfig.child_id==0).all()
    boolconfigs=BoolConfig.query.filter(BoolConfig.child_id==0).all()
    bool_types={c.key:'bool' for c in boolconfigs}

    configs=[*boolconfigs,*strconfigs]
    # categories=sorted([ c for c in {c.key.category():1 for c in configs}])
    # dict_configs={cat:[c for c in configs if c.category==cat] for cat in categories}
    class DynamicForm(FlaskForm):pass
    is_parent=hconfig(ConfigEnum.is_parent)
    for cat in ConfigCategory:
        if cat=='hidden':continue

        cat_configs=[c for c in configs if c.key.category()==cat and (not is_parent or c.key.show_in_parent()) and not c.key.commercial() ]
        if len(cat_configs)==0:continue
        
        class CategoryForm(FlaskForm):
            description_for_fieldset=wtf.fields.TextAreaField("",description=_(f'config.{cat}.description'),render_kw={"class":"d-none"})
        for c in cat_configs:
            if c.key in bool_types:
                field= SwitchField(_(f'config.{c.key}.label'), default=c.value,description=_(f'config.{c.key}.description')) 
            elif c.key==ConfigEnum.lang or c.key==ConfigEnum.admin_lang:
                field=wtf.fields.SelectField(_(f"config.{c.key}.label"),choices=[("en",_("lang.en")),("fa",_("lang.fa")),("zh",_("lang.zh"))],description=_(f"config.{c.key}.description"),default=hconfig(c.key))
            elif c.key==ConfigEnum.country :
                field=wtf.fields.SelectField(_(f"config.{c.key}.label"),choices=[("ir",_("Iran")),("zh",_("China"))],description=_(f"config.{c.key}.description"),default=hconfig(c.key))                
            elif c.key==ConfigEnum.package_mode:
                field=wtf.fields.SelectField(_(f"config.{c.key}.label"),choices=[("release",_("Release")),("develop",_("Develop"))],description=_(f"config.{c.key}.description"),default=hconfig(c.key))
            elif c.key==ConfigEnum.utls:
                field=wtf.fields.SelectField(_(f"config.{c.key}.label"),choices=[("none","None"),("chrome","Chrome"),("edge","Edge"),("ios","iOS"),("android","Android"),("safari","Safari"),("firefox","Firefox"),('random','random'),('randomized','randomized')],description=_(f"config.{c.key}.description"),default=hconfig(c.key))
            elif c.key==ConfigEnum.telegram_lib:
                # if hconfig(ConfigEnum.telegram_lib)=='python':
                #     continue6
                libs=[("python",_("lib.telegram.python")),("tgo",_("lib.telegram.go")),("orig",_("lib.telegram.orignal")),("erlang",_("lib.telegram.erlang"))]
                field=wtf.fields.SelectField(_("config.telegram_lib.label"),choices=libs,description=_("config.telegram_lib.description"),default=hconfig(ConfigEnum.telegram_lib))
            elif c.key in [ConfigEnum.branding_freetext,ConfigEnum.branding_site,ConfigEnum.branding_title]:
                continue
            else:
                render_kw={'class':"ltr"}
                validators=[]
                if c.key==ConfigEnum.domain_fronting_domain:
                    validators.append(wtf.validators.Regexp("^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})|$",re.IGNORECASE,_("config.Invalid domain")))
                    validators.append(hiddify.validate_domain_exist)
                elif '_domain' in c.key:
                    validators.append(wtf.validators.Regexp("^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})$",re.IGNORECASE,_("config.Invalid domain")))
                    validators.append(hiddify.validate_domain_exist)

                    if c.key!=ConfigEnum.decoy_domain:
                        validators.append(wtf.validators.NoneOf([d.domain.lower() for d in Domain.query.all()],_("config.Domain already used")))
                        validators.append(wtf.validators.NoneOf([cc.value.lower() for cc in StrConfig.query.filter(StrConfig.child_id==0).all() if cc.key!=c.key and  "fakedomain" in cc.key and cc.key!=ConfigEnum.decoy_domain],_("config.Domain already used")))
                    render_kw['required']=""
                
                if c.key in [ConfigEnum.parent_panel,ConfigEnum.telegram_bot_token]:
                    continue
                
                if 'secret' in c.key:
                    validators.append(wtf.validators.Regexp("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",re.IGNORECASE,_('config.invalid uuid')))
                    render_kw['required']=""

                if c.key==ConfigEnum.proxy_path:
                    validators.append(wtf.validators.Regexp("^[a-zA-Z0-9]*$",re.IGNORECASE,_("config.Invalid proxy path")))
                    render_kw['required']=""

                if 'port' in c.key:
                    if c.key in [ConfigEnum.http_ports,ConfigEnum.tls_ports]:
                        validators.append(wtf.validators.Regexp("^(\d+)(,\d+)*$",re.IGNORECASE,_("config.Invalid port")))
                        render_kw['required']=""
                    else:    
                        validators.append(wtf.validators.Regexp("^(\d+)(,\d+)*$|^$",re.IGNORECASE,_("config.Invalid port")))

                
                    # validators.append(wtf.validators.Regexp("^(\d+)(,\d+)*$",re.IGNORECASE,_("config.port is required")))
                    
                for val in validators:
                    if hasattr(val,"regex"):
                        render_kw['pattern']=val.regex.pattern
                        render_kw['title']=val.message
                field= wtf.fields.StringField(_(f'config.{c.key}.label'), validators, default=c.value, description=_(f'config.{c.key}.description'),render_kw=render_kw) 
            setattr(CategoryForm,c.key , field)    

        multifield=wtf.fields.FormField(CategoryForm,Markup('<i class="fa-solid fa-plus"></i>&nbsp'+_(f'config.{cat}.label')))
            
        setattr(DynamicForm, cat,  multifield)    

    setattr(DynamicForm,"submit",wtf.fields.SubmitField(_('Submit')))
        

    return DynamicForm()
        
        
    
