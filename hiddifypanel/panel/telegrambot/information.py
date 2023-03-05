from telebot import types
from flask_babelex import gettext as _
from flask import current_app as app

from . import bot
from hiddifypanel.panel.user.user import get_common_data
from ...models import User


@bot.message_handler(commands=['info'])
def send_info(message):
    text = message.text
    user_uuid = text.split()[1] if len(text.split()) > 1 else None
    user = User.query.filter(User.uuid == f'{user_uuid}').first()
    information = get_common_data(user_uuid, 'multi')

    bot.reply_to(message,
                 _("Your hiddify instance information \n" +
                   "Domain: {} \n".format(information['domain']) +
                   "Usage limit: {} GB\n".format(user.usage_limit_GB) +
                   "Current usage: {} GB\n".format(user.current_usage_GB) +
                   "Expires at: {} \n".format(information['expire_s']) +
                   "Remaining days: {} \n".format(information['expire_days']) +
                   "\n\n Happy using \U0001F389 \U0001F389 \U0001F389 \n"
                   ))