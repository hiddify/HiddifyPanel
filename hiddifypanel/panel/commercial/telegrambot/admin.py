from flask_babel import force_locale
from flask_babel import gettext as _
from telebot import types
import datetime

from hiddifypanel.database import db
from hiddifypanel.panel import hiddify
from hiddifypanel.models import *
from hiddifypanel import hutils
from . import bot


@bot.message_handler(commands=['start'], func=lambda message: "admin" in message.text)
def send_welcome(message):
    text = message.text
    # print("dddd",text)
    uuid = text.split()[1].split("_")[1] if len(text.split()) > 1 else None
    if hutils.auth.is_uuid_valid(uuid):
        admin_user = AdminUser.by_uuid(uuid)
        if admin_user:
            admin_user.telegram_id = message.chat.id
            db.session.commit()
    else:
        admin_user = AdminUser.query.filter(AdminUser.telegram_id == message.chat.id).first()

    if admin_user:
        with force_locale(admin_user.lang or hconfig(ConfigEnum.admin_lang)):
            start_admin(message)
        return
    bot.reply_to(message, "error")


def start_admin(message):

    bot.reply_to(message, _("bot.admin_welcome"), reply_markup=admin_keyboard_main())


def get_admin_by_tgid(message):

    tgid = message.chat.id
    return AdminUser.query.filter(AdminUser.telegram_id == tgid).first()


def admin_keyboard_main():

    return types.InlineKeyboardMarkup(keyboard=[[
        types.InlineKeyboardButton(
            text=_("Create Package"),
            callback_data=f'create_package'
        )
    ]
    ]
    )


def admin_keyboard_gig(old_action):
    def keyboard(gig):
        return types.InlineKeyboardButton(
            text=f"{gig} GB",
            callback_data=f"{old_action} {gig}"
        )
    return types.InlineKeyboardMarkup(keyboard=[
        [keyboard(i) for i in range(1, 5)],
        [keyboard(5 * i) for i in range(1, 5)],
        [keyboard(50 * i) for i in range(1, 5)]
    ]
    )


def admin_keyboard_days(old_action):
    def keyboard(days):
        return types.InlineKeyboardButton(
            text=f"{days}",
            callback_data=f"{old_action} {days}"
        )
    return types.InlineKeyboardMarkup(keyboard=[
        [keyboard(i) for i in range(1, 16, 3)],
        [keyboard(30 * i) for i in range(1, 5)]
    ]
    )


def admin_keyboard_count(old_action):
    def keyboard(count):
        return types.InlineKeyboardButton(
            text=f"{count}",
            callback_data=f"{old_action} {count}"
        )
    return types.InlineKeyboardMarkup(keyboard=[
        [keyboard(i) for i in range(1, 5)],
        [keyboard(i * 5) for i in range(1, 5)],
        [keyboard(i * 50) for i in range(1, 5)]
    ]
    )


def admin_keyboard_domain(old_action):
    def keyboard(domain):
        return types.InlineKeyboardButton(
            text=f"{domain.alias or domain.domain}",
            callback_data=f"{old_action} {domain.id}"
        )
    return types.InlineKeyboardMarkup(keyboard=[
        [keyboard(d)]
        for d in Domain.get_domains()
    ]
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith(f'create_package'))
def create_package(call):  # <- passes a CallbackQuery type object to your function
    admin = get_admin_by_tgid(call.message)
    if not (admin):
        return
    with force_locale(admin.lang or hconfig(ConfigEnum.admin_lang)):
        try:
            splt = call.data.split(" ")
            if len(splt) == 1:
                new_text = _("package size?")
                bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=admin_keyboard_gig(call.data))
                bot.answer_callback_query(call.id, text=_("Ok"), show_alert=False, cache_time=1)
            elif len(splt) == 2:
                new_text = _("package days?")
                bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=admin_keyboard_days(call.data))
                bot.answer_callback_query(call.id, text=_("Ok"), show_alert=False, cache_time=1)
            elif len(splt) == 3:
                new_text = _("How many?")
                bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=admin_keyboard_count(call.data))
                bot.answer_callback_query(call.id, text=_("Ok"), show_alert=False, cache_time=1)
            elif len(splt) == 4:
                new_text = _("Domain?")
                bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=admin_keyboard_domain(call.data))
                bot.answer_callback_query(call.id, text=_("Ok"), show_alert=False, cache_time=1)
            elif len(splt) == 5:
                gig = int(splt[1])
                days = int(splt[2])
                count = int(splt[3])
                domain = int(splt[4])
                new_text = _("Please Wait")
                bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=None)
                domain = Domain.query.filter(Domain.id == domain).first()
                from . import Usage
                admin_id = admin.id
                admin_name = admin.name
                for i in range(1, count + 1):
                    new_text = _("Please Wait") + f' {i}/{count}'
                    bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=None)
                    user = User(package_days=days, usage_limit_GB=gig, name=f"{admin_name} auto {i}  {datetime.date.today()}", added_by=admin_id)
                    db.session.add(user)
                    db.session.commit()
                    # bot.send_message(call.message.chat.id,f"Days: {days}     Limit: {gig}GB
                    # #{i}\n\n
                    # https://{domain.domain}/{hconfig(ConfigEnum.proxy_path)}/{user.uuid}/",reply_markup=Usage.user_keyboard(user.uuid))
                    with force_locale(user.lang or hconfig(ConfigEnum.lang)):
                        bot.send_message(call.message.chat.id, Usage.get_usage_msg(user.uuid, domain), reply_markup=Usage.user_keyboard(user.uuid))

                # db.session.commit()
                new_text = _("Finished")
                bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=admin_keyboard_main())
                bot.answer_callback_query(call.id, text=_("Ok"), show_alert=False, cache_time=1)
                from hiddifypanel.panel import usage
                usage.update_local_usage()
                hiddify.quick_apply_users()

        except Exception as e:
            print(e)
            # import traceback
            # traceback.print_stack()
            # new_text=f"Error {e}"
            # bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id,reply_markup=admin_keyboard_main())
            # bot.answer_callback_query(call.id,cache_time =1)
