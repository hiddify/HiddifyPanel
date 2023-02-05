from flask_admin.base import AdminIndexView,expose
from hiddifypanel.panel.hiddify  import admin
from flask import render_template,url_for,Markup
from flask_babelex import lazy_gettext as _
from hiddifypanel.panel import hiddify
from flask_classful import FlaskView
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,hconfig
from hiddifypanel.panel.hiddify import flash
class Dashboard(FlaskView):
    def index(self):
        # try:
            def_user=None if len(User.query.all())>1 else User.query.filter(User.name=='default').first()
            domains=Domain.query.all()
            sslip_domains=[d.domain for d in domains if "sslip.io" in d.domain]

            if def_user and sslip_domains:
                quick_setup=url_for("admin.QuickSetup:index")
                flash((_('It seems that you have not setup the system completely. <a class="btn btn-success" href="%(quick_setup)s">Click here</a> to complete setup.',quick_setup=quick_setup)),'warning')
            elif len(sslip_domains):
                flash((_('It seems that you are using default domain (%(domain)s) which is not recommended.',domain=sslip_domains[0])),'warning')
            elif def_user:
                d=domains[0]
                u=def_user.uuid
                flash((_('It seems that you have not created any users yet. Default user link: %(default_link)s',default_link=hiddify.get_user_link(u,d))),'secondary')
            
        # except:
        #     flash((_('Error!!!')),'info')
            return render_template('index.html')