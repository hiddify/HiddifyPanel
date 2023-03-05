from telebot import types
from flask_babelex import gettext as _
from flask import current_app as app

from . import bot
from hiddifypanel.panel.user.user import get_common_data
from ...models import User


def prepare_me_info(user):
    pass


def prepare_help_message():
    commands = {  # command description used in the "help" command
        'start': 'Get started with the the bot',
        'help': 'Gives you information about the available commands',
        'info': 'Return information about your usages',
        'me': 'Return information about your account'
    }

    response = "The following commands are available: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        response += "/" + key + ": "
        response += commands[key] + "\n"

    return response


def prepare_welcome_message():
    response = _("Hooray \U0001F389 \U0001F389 \U0001F389 \n"
                 "Welcome to hiddifybot.\n"
                 "Start by clicking the link on the panel or entering your UUID.")

    return response


@bot.message_handler(commands=['help'])
def command_me(message):
    bot.reply_to(message, prepare_help_message())


@bot.message_handler(commands=['help'])
def command_help(message):
    bot.reply_to(message, prepare_help_message())


@bot.message_handler(commands=['start'])
def command_start(message):
    text = message.text
    user_uuid = text.split()[1] if len(text.split()) > 1 else None
    bot.reply_to(message, prepare_welcome_message())


@bot.message_handler(commands=['info'])
def command_info(message):
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
