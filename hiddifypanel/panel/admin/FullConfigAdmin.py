from hiddifypanel.models import BoolConfig,StrConfig,ConfigEnum,hconfig
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
    # return "d"
    import flask_babelex
    

    # form=HelloForm()
    # # return render('config.html',form=form)
    # return render_template('config.html',form=HelloForm())
    form=get_config_form()
    return render_template('config.html',form=form)


def save():
    form=get_config_form()
    if form.validate_on_submit():
        
        boolconfigs=BoolConfig.query.all()
        bool_types={c.key:'bool' for c in boolconfigs}
        for cat,vs in form.data.items():#[c for c in ConfigEnum]:
        
            if type(vs) is dict:
                for k,v in vs.items():
        
                    if k in [c for c in ConfigEnum]:
                        if k in bool_types:
                            BoolConfig.query.filter(BoolConfig.key==k).first().value=v
                        else:
                            StrConfig.query.filter(StrConfig.key==k).first().value=v
                
            # print(cat,vs)
        db.session.commit()
        apply_btn=f"<a href='{url_for('admin.actions.apply_configs')}' class='btn btn-primary'>"+_("admin.config.apply_configs")+"</a>"
        flash(Markup(_('config.validation-success',link=apply_btn)), 'success')

        return render_template('config.html', form=form)
    flash(_('config.validation-error'), 'danger')
    return render_template('config.html', form=form)

    
    import flask_babelex
    

    # form=HelloForm()
    # # return render('config.html',form=form)
    # return render_template('config.html',form=HelloForm())
    form=get_config_form()
    return render_template('config.html',form=form)

def get_babel_string():
    res=""
    strconfigs=StrConfig.query.all()
    boolconfigs=BoolConfig.query.all()
    bool_types={c.key:'bool' for c in boolconfigs}

    configs=[*boolconfigs,*strconfigs]
    categories=sorted([ c for c in {c.category:1 for c in configs}])

    for cat in categories:
        if cat=='hidden':continue

        cat_configs=[c for c in configs if c.category==cat]
        
        for c in cat_configs:
            res+=f'{{{{_("config.{c.key}.label")}}}} {{{{_("config.{c.key}.description")}}}}'
            

        res+=f'{{{{_("config.{cat}.label")}}}}{{{{_("config.{cat}.description")}}}}'
    for c in ConfigEnum:
        res+=f'{{{{_("config.{c}.label")}}}} {{{{_("config.{c}.description")}}}}'
    return res
    

def get_config_form():
    
    
    strconfigs=StrConfig.query.all()
    boolconfigs=BoolConfig.query.all()
    bool_types={c.key:'bool' for c in boolconfigs}

    configs=[*boolconfigs,*strconfigs]
    categories=sorted([ c for c in {c.category:1 for c in configs}])
    # dict_configs={cat:[c for c in configs if c.category==cat] for cat in categories}
    class DynamicForm(FlaskForm):pass

    for cat in categories:
        if cat=='hidden':continue

        cat_configs=[c for c in configs if c.category==cat]
        class CategoryForm(FlaskForm):
            description_for_fieldset=wtf.fields.TextAreaField("",description=_(f'config.{cat}.description'),render_kw={"class":"d-none"})
        for c in cat_configs:
            if c.key in bool_types:
                field= SwitchField(_(f'config.{c.key}.label'), default=c.value,description=_(f'config.{c.key}.description')) 
            elif c.key==ConfigEnum.lang:
                field=wtf.fields.SelectField(_("config.lang.label"),choices=[("en",_("lang.en")),("fa",_("lang.fa"))],description=_("config.lang.description"),default=hconfig(ConfigEnum.lang))
            else:
                render_kw={'class':"ltr"}
                validators=[]
                if c.key==ConfigEnum.domain_fronting_domain:
                    validators.append(wtf.validators.Regexp("^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})|$",re.IGNORECASE,_("config.Invalid domain")))
                elif 'domain' in c.key:
                    validators.append(wtf.validators.Regexp("^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})$",re.IGNORECASE,_("config.Invalid domain")))
                    validators.append(wtf.validators.NoneOf(db.session.query(Domain.domain).all(),_("config.Domain already used")))
                    render_kw['required']=""
        

                if c.key==ConfigEnum.decoy_site:
                    validators.append(wtf.validators.Regexp("http(s|)://([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})/?",re.IGNORECASE,_("config.Invalid decoy_site")))
                    render_kw['required']=""

                if 'secret' in c.key:
                    validators.append(wtf.validators.Regexp("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",re.IGNORECASE,_('config.invalid uuid')))
                    render_kw['required']=""

                if c.key==ConfigEnum.proxy_path:
                    validators.append(wtf.validators.Regexp("^[a-zA-Z0-9]*$",re.IGNORECASE,_("config.Invalid proxy path")))
                    render_kw['required']=""

                if 'port' in c.key:
                    validators.append(wtf.validators.Regexp("^(\d,?)*$",re.IGNORECASE,_("config.Invalid port")))

                if c.key==ConfigEnum.http_ports:
                    validators.append(wtf.validators.Regexp("^(\d,?)*80(\d,?)*$",re.IGNORECASE,_("config.port 80 is required")))
                    render_kw['required']=""
                if c.key==ConfigEnum.tls_ports:
                    validators.append(wtf.validators.Regexp("^(\d,?)*443(\d,?)*$",re.IGNORECASE,_("config.port 443 is required")))
                    render_kw['required']=""
                for val in validators:
                    if hasattr(val,"regex"):
                        render_kw['pattern']=val.regex.pattern
                        render_kw['title']=val.message
                field= wtf.fields.StringField(_(f'config.{c.key}.label'), validators, default=c.value, description=_(f'config.{c.key}.description'),render_kw=render_kw) 
            setattr(CategoryForm,c.key , field)    

        multifield=wtf.fields.FormField(CategoryForm,_(f'config.{cat}.label'))
            
        setattr(DynamicForm, cat,  multifield)    

    setattr(DynamicForm,"submit",wtf.fields.SubmitField(_('Submit')))
        

    return DynamicForm()
        
        
    
