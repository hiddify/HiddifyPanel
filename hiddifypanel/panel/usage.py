from flask_babel import lazy_gettext as _
from sqlalchemy import func
from typing import Dict
import datetime

from hiddifypanel.drivers import user_driver
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
from hiddifypanel.database import db
from hiddifypanel import cache, hutils
from loguru import logger
to_gig_d = 1024**3


def update_local_usage():
    lock_key = "lock-update-local-usage"
    if not cache.redis_client.set(lock_key, "locked", nx=True, ex=600):
        return {"msg": "last update task is not finished yet."}
    try:
        res = user_driver.get_users_usage(reset=True)
        # cache.redis_client.delete(lock_key)
        cache.redis_client.set(lock_key, "locked", nx=False, ex=60)
        return _add_users_usage(res, child_id=0)
    except Exception as e:
        cache.redis_client.set(lock_key, "locked", nx=False, ex=60)
        logger.exception("Exception in update usage")
        raise
        return {"msg": f"Exception in update usage: {e}"}

    # return {"status": 'success', "comments":res}


def add_users_usage_uuid(uuids_bytes: Dict[str, Dict], child_id, sync=False):
    uuids_bytes = {u: v for u, v in uuids_bytes.items() if v}
    uuids = uuids_bytes.keys()
    users = User.query.filter(User.uuid.in_(uuids))
    dbusers_bytes = {u: uuids_bytes.get(u.uuid, 0) for u in users}
    _add_users_usage(dbusers_bytes, child_id, sync)  # type: ignore


def _reset_priodic_usage():
    last_usage_check: int = hconfig(ConfigEnum.last_priodic_usage_check) or 0
    import time
    current_time = int(time.time())
    if current_time - last_usage_check < 60 * 60 * 6:
        return
    # reset as soon as possible in the day
    if datetime.datetime.now().hour > 5 and current_time - last_usage_check < 60 * 60 * 24:
        return
    logger.debug("reseting user usage if needed")
    for user in User.query.filter(User.mode != UserMode.no_reset).all():
        if user.user_should_reset():
            logger.info(f"reseting user usage for {user.uuid}")
            user.reset_usage(commit=False)
    set_hconfig(ConfigEnum.last_priodic_usage_check, current_time)


def _add_users_usage(users_usage_data: Dict[User, Dict], child_id, sync=False):
    '''
    sync: when enabled, it means we have received usages from the parent panel
    '''
    res = {}
    have_change = False
    before_enabled_users = user_driver.get_enabled_users()

    daily_usage = {}
    today = datetime.date.today()
    changes = False
    for adm in AdminUser.query.all():
        daily_usage[adm.id] = DailyUsage.query.filter(DailyUsage.date == today, DailyUsage.admin_id == adm.id, DailyUsage.child_id == child_id).first()
        if daily_usage[adm.id] is None:
            logger.info(f"creating a new daily usage {today} admin={adm.id} child={child_id}")
            daily_usage[adm.id] = DailyUsage(date=today, admin_id=adm.id, child_id=child_id)
            db.session.add(daily_usage[adm.id])
            changes = True
        daily_usage[adm.id].online = User.query.filter(User.added_by == adm.id).filter(func.DATE(User.last_online) == today).count()
    if changes:
        db.session.commit()
    _reset_priodic_usage()

    # userDetails = {p.user_id: p for p in UserDetail.query.filter(UserDetail.child_id == child_id).all()}
    for user, uinfo in users_usage_data.items():
        usage_bytes = uinfo['usage']

        # UserDetails things
        # detail = UserDetail(user_id=user.id, child_id=child_id)
        # detail = userDetails.get(user.id)
        # if not detail:
        #     detail = UserDetail(user_id=user.id, child_id=child_id)
        #     db.session.add(detail)
        # if uinfo['devices'] != detail.connected_devices:
        #     detail.connected_devices = uinfo['devices']

        # Enable the user if isn't already
        if not before_enabled_users[user.uuid] and user.is_active:
            logger.info(f"Enabling disabled client {user.uuid} ")
            user_driver.add_client(user)
            send_bot_message(user)
            have_change = True

        # Check if there's new usage value
        if not isinstance(usage_bytes, int) or usage_bytes == 0:
            res[user.uuid] = "No usage"
        else:
            # Set new daily usage of the user
            if sync and daily_usage.get(user.added_by, daily_usage[1]).usage != usage_bytes:
                daily_usage.get(user.added_by, daily_usage[1]).usage = usage_bytes
            else:
                daily_usage.get(user.added_by, daily_usage[1]).usage += usage_bytes

            in_bytes = usage_bytes

            # Set new current usage of the user
            if sync and user.current_usage != in_bytes:
                user.current_usage = in_bytes
                # detail.current_usage_GB = in_gig
            else:
                user.current_usage += in_bytes
                # detail.current_usage = detail.current_usage or 0
                # detail.current_usage += in_bytes

            # Change last online time of the user
            user.last_online = datetime.datetime.now()
            # detail.last_online = datetime.datetime.now()

            # Set start date of user to the current datetime if it hasn't been set already
            if user.start_date is None:
                user.start_date = datetime.date.today()

            res[user.uuid] = f'{in_bytes/1000000:0.3f}MB'

        # Remove user from drivers(singbox, xray, wireguard etc.) if they're inactive
        # print(before_enabled_users[user.uuid], user.is_active)
        if before_enabled_users[user.uuid] and not user.is_active:
            logger.info(f"Removing enabled client {user.uuid} ")

            user_driver.remove_client(user)
            have_change = True
            res[user.uuid] = f"{res[user.uuid]} !OUT of USAGE! Client Removed"

    db.session.commit()  # type: ignore

    # Remove invalid users
    for uuid in before_enabled_users:
        if uuid in res:
            continue

        user = User.query.filter(User.uuid == uuid).first()
        if not user:
            user_driver.remove_client(User(uuid=uuid))
        elif not user.is_active:
            user_driver.remove_client(user)

    # print("------------------", res)
    # Apply the changes to the drivers
    if have_change:
        hiddify.quick_apply_users()

    # Sync the new data with the parent node if the data has not been set by the parent node itself and the current panel is a child panel
    if not sync and hutils.node.is_child():
        hutils.node.child.sync_users_usage_with_parent()

    return {"status": 'success', "comments": res, "date": hutils.convert.time_to_json(datetime.datetime.now())}


def send_bot_message(user):
    if not (hconfig(ConfigEnum.telegram_bot_token) or hutils.node.is_child()):
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
