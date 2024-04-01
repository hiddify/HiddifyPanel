from flask_babel import lazy_gettext as _
from sqlalchemy import func
from typing import Dict
import datetime

from hiddifypanel.drivers import user_driver
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
from hiddifypanel.database import db
from hiddifypanel import hutils

to_gig_d = 1024**3


def update_local_usage():
    res = user_driver.get_users_usage(reset=True)
    return _add_users_usage(res, child_id=0)

    # return {"status": 'success', "comments":res}


def add_users_usage_uuid(uuids_bytes: Dict[str, Dict], child_id, sync=False):
    uuids_bytes = {u: v for u, v in uuids_bytes.items() if v}
    uuids = uuids_bytes.keys()
    users = User.query.filter(User.uuid.in_(uuids))
    dbusers_bytes = {u: uuids_bytes.get(u.uuid, 0) for u in users}
    _add_users_usage(dbusers_bytes, child_id, sync)  # type: ignore


def _add_users_usage(users_usage_data: Dict[User, Dict], child_id, sync=False):
    '''
    sync: when enabled, it means we have received usages from the parent panel
    '''
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
    for user, uinfo in users_usage_data.items():
        usage_bytes = uinfo['usage']
        devices = uinfo['devices']
        # user_active_before=user.is_active
        detail = userDetails.get(user.id)
        if not detail:
            detail = UserDetail(user_id=user.id, child_id=child_id)
            detail.current_usage_GB = detail.current_usage_GB or 0
            db.session.add(detail)
        detail.connected_devices = devices
        detail.current_usage_GB = detail.current_usage_GB or 0
        if not user.last_reset_time or user.user_should_reset():
            user.last_reset_time = datetime.date.today()
            user.current_usage_GB = 0
            detail.current_usage_GB = 0

        if not before_enabled_users[user.uuid] and user.is_active:
            print(f"Enabling disabled client {user.uuid} ")
            user_driver.add_client(user)
            send_bot_message(user)
            have_change = True
        if not isinstance(usage_bytes, int) or usage_bytes == 0:
            res[user.uuid] = "No usage"
        else:
            if sync:
                if daily_usage.get(user.added_by, daily_usage[1]).usage != usage_bytes:
                    daily_usage.get(user.added_by, daily_usage[1]).usage = usage_bytes
            else:
                daily_usage.get(user.added_by, daily_usage[1]).usage += usage_bytes
            in_gig = (usage_bytes) / to_gig_d
            res[user.uuid] = in_gig
            if sync:
                if user.current_usage_GB != in_gig:
                    user.current_usage_GB = in_gig
                # detail.current_usage_GB = in_gig
            else:
                user.current_usage_GB += in_gig
                detail.current_usage_GB += in_gig
            user.last_online = datetime.datetime.now()
            detail.last_online = datetime.datetime.now()

            if user.start_date is None:
                user.start_date = datetime.date.today()

        if before_enabled_users[user.uuid] and not user.is_active:
            print(f"Removing enabled client {user.uuid} ")
            user_driver.remove_client(user)
            have_change = True
            res[user.uuid] = f"{res[user.uuid]} !OUT of USAGE! Client Removed"

    db.session.commit()  # type: ignore
    if have_change:
        hiddify.quick_apply_users()

    # sync with the parent
    if not sync:
        if hutils.node.is_child():
            hutils.node.child.sync_users_usage_with_parent()
    return {"status": 'success', "comments": res}


def send_bot_message(user):
    if not (hconfig(ConfigEnum.telegram_bot_token) or not hutils.node.is_parent()):
        return
    if not user.telegram_id:
        return
    from hiddifypanel.panel.commercial.telegrambot import bot, Usage
    try:
        msg = Usage.get_usage_msg(user.uuid)
        msg = _("User activated!") if user.is_active else _("Package ended!") + "\n" + msg
        bot.send_message(user.telegram_id, msg, reply_markup=Usage.user_keyboard(user.uuid))
    except BaseException:
        pass
