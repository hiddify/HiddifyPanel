from hiddifypanel.panel import hiddify
from sqlalchemy.orm import Load, joinedload


from hiddifypanel.drivers import user_driver
from sqlalchemy import func
from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _
import urllib
from hiddifypanel.models import *
from hiddifypanel.panel.database import db
import datetime
from flask import jsonify, g, url_for, Markup
from flask import flash as flask_flash
to_gig_d = 1024**3


def update_local_usage():
    res = user_driver.get_users_usage(reset=True)
    return add_users_usage(res, child_id=0)

    # return {"status": 'success', "comments":res}


def add_users_usage_uuid(uuids_bytes, child_id):
    users = User.query.filter(User.uuid.in_(keys(uuids_bytes)))
    dbusers_bytes = {u: uuids_bytes.get(u.uuid, 0) for u in users}
    add_users_usage(dbusers_bytes, child_id)


def add_users_usage(dbusers_bytes, child_id):
    print(dbusers_bytes)
    if not hconfig(ConfigEnum.is_parent) and hconfig(ConfigEnum.parent_panel):
        from hiddifypanel.panel import hiddify_api
        hiddify_api.add_user_usage_to_parent(dbusers_bytes)

    res = {}
    have_change = False
    before_enabled_users = user_driver.get_enabled_users()
    daily_usage = {}
    today = datetime.date.today()
    for adm in AdminUser.query.all():
        daily_usage[adm.id] = DailyUsage.query.filter(DailyUsage.date == today, DailyUsage.admin_id == adm.id, DailyUsage.child_id == child_id).first()
        if not daily_usage[adm.id]:
            daily_usage[adm.id] = DailyUsage(admin_id=adm.id, child_id=child_id)
            db.session.add(daily_usage[adm.id])
        daily_usage[adm.id].online = User.query.filter(User.added_by == adm.id).filter(func.DATE(User.last_online) == today).count()
    # db.session.commit()
    userDetails = {p.user_id: p for p in UserDetail.query.filter(UserDetail.child_id == child_id).all()}
    for user, uinfo in dbusers_bytes.items():
        usage_bytes = uinfo['usage']
        ips = uinfo['ips']
        # user_active_before=is_user_active(user)
        detail = userDetails.get(user.id)
        if not detail:
            detail = UserDetail(user_id=user.id, child_id=child_id)
            detail.current_usage_GB = detail.current_usage_GB or 0
            db.session.add(detail)
        detail.connected_ips = ips
        detail.current_usage_GB = detail.current_usage_GB or 0
        if not user.last_reset_time or user_should_reset(user):
            user.last_reset_time = datetime.date.today()
            user.current_usage_GB = 0
            detail.current_usage_GB = 0

        if not before_enabled_users[user.uuid] and user.is_active:
            print("Enabling disabled client {user.uuid} ")
            user_driver.add_client(user)
            send_bot_message(user)
            have_change = True
        if type(usage_bytes) != int or usage_bytes == 0:
            res[user.uuid] = "No usage"
        else:
            daily_usage.get(user.added_by, daily_usage[1]).usage += usage_bytes
            in_gig = (usage_bytes)/to_gig_d
            res[user.uuid] = in_gig
            user.current_usage_GB += in_gig
            detail.current_usage_GB += in_gig
            user.last_online = datetime.datetime.now()
            detail.last_online = datetime.datetime.now()

            if user.start_date == None:
                user.start_date = datetime.date.today()

        if before_enabled_users[user.uuid] and not is_user_active(user):
            print("Removing enabled client {user.uuid} ")
            user_driver.remove_client(user)
            have_change = True
            res[user.uuid] = f"{res[user.uuid]} !OUT of USAGE! Client Removed"

    db.session.commit()
    if have_change and hconfig(ConfigEnum.core_type == 'singbox'):
        hiddify.quick_apply_users()

    return {"status": 'success', "comments": res}


def send_bot_message(user):
    if not (hconfig(ConfigEnum.telegram_bot_token) and not hconfig(ConfigEnum.parent_panel)):
        return
    if not user.telegram_id:
        return
    from hiddifypanel.panel.commercial.telegrambot import bot, Usage
    try:
        msg = Usage.get_usage_msg(user.uuid)
        msg = _("User activated!") if is_user_active(user) else _("Package ended!")+"\n"+msg
        bot.send_message(user.telegram_id, msg, reply_markup=Usage.user_keyboard(uuid))
    except:
        pass
