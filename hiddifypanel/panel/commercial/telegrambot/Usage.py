from hiddifypanel.panel import hiddify
from telebot import types
from flask_babel import gettext as _
from flask_babel import force_locale
from flask import current_app as app
from hiddifypanel.models import *
from . import bot
from hiddifypanel.panel.user.user import get_common_data
from hiddifypanel.database import db
from hiddifypanel import hutils


@bot.message_handler(func=lambda message: "admin" not in message.text)
def send_usage(message):
    return send_welcome(message)


@bot.message_handler(commands=['start'], func=lambda message: "admin" not in message.text)
def send_welcome(message):
    text = message.text
    uuid = text.split()[-1] if len(text.split()) > 0 else None
    if hutils.auth.is_uuid_valid(uuid):
        user = User.by_uuid(uuid)
        if user:
            user.telegram_id = message.chat.id
            db.session.commit()
    else:
        user = User.query.filter(User.telegram_id == message.chat.id).first()
    if user:
        with force_locale(user.lang or hconfig(ConfigEnum.lang)):
            bot.reply_to(message, get_usage_msg(user.uuid), reply_markup=user_keyboard(user.uuid))
    else:
        bot.reply_to(message, _("bot.welcome"))


def user_keyboard(uuid):
    return types.InlineKeyboardMarkup(
        keyboard=[
            [
                types.InlineKeyboardButton(
                    text=_("update"),
                    callback_data="update_usage " + uuid
                )
            ]
        ]
    )


def get_usage_msg(uuid, domain=None):
    user_data = get_common_data(uuid, 'multi')
    with app.app_context():

        user = user_data['user']
        expire_rel = user_data['expire_rel']
        reset_day = user_data['reset_day']

        domain = domain or Domain.get_domains()[0]
        user_link = hiddify.get_account_panel_link(user, domain.domain)
        with force_locale(user.lang or hconfig(ConfigEnum.lang)):
            msg = f"""{_('<a href="%(user_link)s"> %(user)s</a>',user_link=user_link ,user=user.name if user.name != "default" else "")}\n\n"""

            msg += f"""{_('user.home.usage.title')} {round(user.current_usage_GB, 3)}GB <b>{_('user.home.usage.from')}</b> {user.usage_limit_GB}GB  {_('user.home.usage.monthly') if user.monthly else ''}\n"""
            msg += f"""<b>{_('user.home.usage.expire')}</b> {expire_rel}"""

            if reset_day < 500:
                msg += f"""\n<b>{_('Reset Usage Time:')}</b> {reset_day} {_('days')}"""

            msg += f"""\n\n <a href="{user_link}">{_("Home Link")}</a>  -  <a href="https://t.me/{bot.username}?start={user.uuid}">{_("Telegram Bot Link")}</a>"""
    return msg


@bot.callback_query_handler(func=lambda call: call.data.startswith("update_usage"))
def update_usage_callback(call):  # <- passes a CallbackQuery type object to your function
    text = call.data
    uuid = text.split()[1] if len(text.split()) > 1 else None

    if uuid:
        user = User.by_uuid(uuid)
        try:
            with force_locale(f'{user.lang or hconfig(ConfigEnum.lang)}'):
                new_text = get_usage_msg(uuid)
                bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=user_keyboard(uuid))
                bot.answer_callback_query(call.id, text='Updated', show_alert=False, cache_time=1)
        except Exception as e:
            print(e)
            try:
                bot.answer_callback_query(call.id, cache_time=1)
            except BaseException:
                pass
