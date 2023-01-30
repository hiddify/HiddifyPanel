from hiddifypanel.models import BoolConfig,StrConfig,ConfigEnum,hconfig
# from flask_babelex import lazy_gettext as __
from flask_babelex import gettext as _
import wtforms as wtf
from flask_wtf import FlaskForm, CSRFProtect
from flask_bootstrap import SwitchField

from flask_admin.base import expose
# from gettext import gettext as _


import re
from flask import render_template,current_app,flash, Markup
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
        flash(_('config.validation-success'), 'success')
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
        class CategoryForm(FlaskForm):pass
        for c in cat_configs:
            if c.key in bool_types:
                field= SwitchField(_(f'config.{c.key}.label'), default=c.value,description=_(f'config.{c.key}.description')) 
            else:
                validators=[]
                if 'domain' in c.key:
                    validators.append(wtf.validators.Regexp("^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})$",re.IGNORECASE,_("config.Invalid domain")))
                    validators.append(wtf.validators.NoneOf(db.session.query(Domain.domain).all(),_("config.Domain already used")))

                if c.key==ConfigEnum.decoy_site:
                    validators.append(wtf.validators.Regexp("http(s|)://([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})/?",re.IGNORECASE,_("config.Invalid decoy_site")))

                if 'secret' in c.key:
                    validators.append(wtf.validators.UUID(_('config.invalid uuid')))

                if c.key==ConfigEnum.proxy_path:
                    validators.append(wtf.validators.Regexp("^[a-zA-Z0-9]*$",re.IGNORECASE,_("config.Invalid proxy path")))

                if 'port' in c.key:
                    validators.append(wtf.validators.Regexp("^(\d,?)*$",re.IGNORECASE,_("config.Invalid port")))

                if c.key==ConfigEnum.lang:
                    validators.append(wtf.validators.AnyOf(["en","fa"]))
                if c.key==ConfigEnum.http_ports:
                    validators.append(wtf.validators.Regexp("^(\d,?)*80(\d,?)*$",re.IGNORECASE,_("config.port 80 is required")))
                if c.key==ConfigEnum.tls_ports:
                    validators.append(wtf.validators.Regexp("^(\d,?)*443(\d,?)*$",re.IGNORECASE,_("config.port 443 is required")))

                field= wtf.fields.StringField(_(f'config.{c.key}.label'), validators, default=c.value, description=_(f'config.{c.key}.description'),render_kw={'class':"ltr"}) 
            setattr(CategoryForm,c.key , field)    

        multifield=wtf.fields.FormField(CategoryForm,_(f'config.{cat}.label'),description=_(f'config.{cat}.description'))
            
        setattr(DynamicForm, cat,  multifield)    

    setattr(DynamicForm,"submit",wtf.fields.SubmitField(_('Submit')))
        

    return DynamicForm()
        
        
    
