from flask_admin.base import AdminIndexView, expose
from hiddifypanel.panel.hiddify import admin
from flask import render_template, url_for, Markup, request, jsonify, g, redirect
from flask_babelex import lazy_gettext as _
from hiddifypanel.panel import hiddify
import datetime
from flask_classful import FlaskView, route
from hiddifypanel.models import *
from hiddifypanel.panel.database import db
from hiddifypanel.panel.hiddify import flash
import hiddifypanel


class Dashboard(FlaskView):
    def get_data(self):
        admin_id = request.args.get("admin_id") or g.admin.id
        if admin_id not in g.admin.recursive_sub_admins_ids():
            abort(403, _("Access Denied!"))

        return jsonify(dict(
            stats={'system': hiddify.system_stats(), 'top5': hiddify.top_processes()},
            usage_history=get_daily_usage_stats(admin_id)
        ))

    def index(self):
        print(hconfig(ConfigEnum.first_setup))
        if hconfig(ConfigEnum.first_setup):
            return redirect(url_for("admin.QuickSetup:index"))
        if hiddifypanel.__release_date__ + datetime.timedelta(days=20) < datetime.datetime.now():
            flash(_('This version of hiddify panel is outdated. Please update it from admin area.'), "danger")
        bot = None
        # if hconfig(ConfigEnum.license):
        childs = None
        admin_id = request.args.get("admin_id") or g.admin.id
        if admin_id not in g.admin.recursive_sub_admins_ids():
            abort(403, _("Access Denied!"))

        child_id = request.args.get("child_id") or None
        user_query = User.query
        if admin_id:
            user_query = user_query.filter(User.added_by == admin_id)
        if hconfig(ConfigEnum.is_parent):
            childs = Child.query.filter(Child.id != 0).all()
            for c in childs:
                c.is_active = False
                for d in c.domains:
                    if d.mode == DomainType.fake:
                        continue
                    remote = f"https://{d.domain}/{hconfig(ConfigEnum.proxy_path,c.id)}/{hconfig(ConfigEnum.admin_secret,c.id)}"
                    d.is_active = hiddify.check_connection_to_remote(remote)
                    if d.is_active:
                        c.is_active = True

            # return render_template('parent_dash.html',childs=childs,bot=bot)
    # try:
        def_user = None if len(User.query.all()) > 1 else User.query.filter(User.name == 'default').first()
        domains = get_panel_domains()
        sslip_domains = [d.domain for d in domains if "sslip.io" in d.domain]

        if def_user and sslip_domains:
            quick_setup = url_for("admin.QuickSetup:index")
            flash((_('It seems that you have not setup the system completely. <a class="btn btn-success" href="%(quick_setup)s">Click here</a> to complete setup.', quick_setup=quick_setup)), 'warning')
            if hconfig(ConfigEnum.is_parent):
                flash(_("Please understand that parent panel is under test and the plan and the condition of use maybe change at anytime."), "danger")
        elif len(sslip_domains):
            flash((_('It seems that you are using default domain (%(domain)s) which is not recommended.', domain=sslip_domains[0])), 'warning')
            if hconfig(ConfigEnum.is_parent):
                flash(_("Please understand that parent panel is under test and the plan and the condition of use maybe change at anytime."), "danger")
        elif def_user:
            d = domains[0]
            u = def_user.uuid
            flash((_('It seems that you have not created any users yet. Default user link: %(default_link)s', default_link=hiddify.get_user_link(u, d))), 'secondary')

    # except:
    #     flash((_('Error!!!')),'info')

        stats = {'system': hiddify.system_stats(), 'top5': hiddify.top_processes()}
        return render_template('index.html', stats=stats, usage_history=get_daily_usage_stats(admin_id, child_id), childs=childs)

    @route('remove_child', methods=['POST'])
    def remove_child(self):
        child_id = request.form['child_id']
        child = Child.query.filter(Child.id == child_id).first()
        db.session.delete(child)
        db.session.commit()
        flash(_("child has been removed!"), "success")
        return self.index()
