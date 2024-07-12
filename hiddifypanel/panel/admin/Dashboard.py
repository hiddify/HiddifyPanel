from flask import render_template, request, g, redirect
from hiddifypanel.hutils.flask import hurl_for
from flask_classful import FlaskView, route
from flask_babel import lazy_gettext as _
from apiflask import abort
import datetime


from hiddifypanel.auth import login_required
from hiddifypanel.database import db
from hiddifypanel.panel import hiddify
from hiddifypanel.models import *
from hiddifypanel import hutils
import hiddifypanel


class Dashboard(FlaskView):

    @login_required(roles={Role.super_admin, Role.admin, Role.agent})
    def index(self):
        if hconfig(ConfigEnum.first_setup):
            return redirect(hurl_for("admin.QuickSetup:index"))

        if hutils.utils.is_panel_outdated():
            hutils.flask.flash(_('outdated_panel'), "danger")  # type: ignore

        childs = None
        admin_id = request.args.get("admin_id") or g.account.id
        if admin_id not in g.account.recursive_sub_admins_ids():
            abort(403, _("Access Denied!"))

        child_id = request.args.get("child_id") or None
        user_query = User.query
        if admin_id:
            user_query = user_query.filter(User.added_by == admin_id)
        if hutils.node.is_parent():
            childs = Child.query.filter(Child.id != 0).all()
            for c in childs:
                c.is_active = False
                for d in c.domains:
                    d.is_active = hutils.node.parent.is_child_domain_active(c, d)
                    if d.is_active:
                        c.is_active = True

        def_user = None if len(User.query.all()) > 1 else User.query.filter(User.name == 'default').first()
        domains = Domain.get_domains()
        sslip_domains = [d.domain for d in domains if "sslip.io" in d.domain]

        if def_user and sslip_domains:
            quick_setup = hurl_for("admin.QuickSetup:index")
            hutils.flask.flash((_('admin.incomplete_setup_warning', quick_setup=quick_setup)), 'warning')  # type: ignore
            if hutils.node.is_parent():
                hutils.flask.flash(
                    _("Please understand that parent panel is under test and the plan and the condition of use maybe change at anytime."), "danger")  # type: ignore
        elif len(sslip_domains):
            hutils.flask.flash((_('It seems that you are using default domain (%(domain)s) which is not recommended.',
                               domain=sslip_domains[0])), 'warning')  # type: ignore
            if hutils.node.is_parent():
                hutils.flask.flash(
                    _("Please understand that parent panel is under test and the plan and the condition of use maybe change at anytime."), "danger")  # type: ignore
        elif def_user:
            d = domains[0]
            hutils.flask.flash((_("admin.no_user_warning",
                               default_link=hiddify.get_html_user_link(def_user, d))), 'secondary')  # type: ignore
        if hutils.network.is_ssh_password_authentication_enabled():
            hutils.flask.flash(_('serverssh.password-login.warning'), "warning")  # type: ignore

    # except:
    #     hutils.flask.flash((_('Error!!!')),'info')

        stats = {'system': hutils.system.system_stats(), 'top5': hutils.system.top_processes()}
        return render_template('index.html', stats=stats, usage_history=DailyUsage.get_daily_usage_stats(admin_id, child_id), childs=childs)

    @ login_required(roles={Role.super_admin})
    @ route('remove_child', methods=['POST'])
    def remove_child(self):
        child_id = request.form['child_id']
        child = Child.query.filter(Child.id == child_id).first()
        db.session.delete(child)
        db.session.commit()
        hutils.flask.flash(_("child has been removed!"), "success")  # type: ignore
        return self.index()
