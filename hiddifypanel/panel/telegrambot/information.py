from telebot import types
from flask_babelex import gettext as _
from flask import current_app as app

from . import bot
from hiddifypanel.panel.user.user import get_common_data


@bot.message_handler(commands=['info'])
def send_info(message):
    text = message.text
    uuid = text.split()[1] if len(text.split()) > 1 else None
    information = get_common_data(uuid, 'multi')

    bot.reply_to(message,
                 _("Your hiddify instance information \n" +
                   "Domain: {} \n".format(information['domain']) +
                   "Usage limit: {} \n".format(information['usage_limit_b']) +
                   "Current usage: {} \n".format(information['usage_current_b']) +
                   "Expires at: {} \n".format(information['expire_s']) +
                   "Remaining days: {} \n".format(information['expire_days']) +
                   "\n\n Happy using \U0001F389 \U0001F389 \U0001F389 \n"
                   ))