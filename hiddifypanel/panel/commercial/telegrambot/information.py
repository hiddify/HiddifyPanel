from flask_babel import gettext as _

from hiddifypanel.panel.user.user import get_common_data
from hiddifypanel.models import User
from . import bot


def prepare_me_info(user):
    """
    Prepare response to the "me" command
    @param user: User instance
    @return: A text message
    """

    response = _("Dear {}\n\n".format(user.name if user.name is not None else "user") +
                 "Your hiddify information is\n" +
                 "UUID: {}\n".format(user.uuid) +
                 "Last online date: {}\n".format(user.last_online) +
                 "Expire time: {}\n".format(user.remaining_days) +
                 "Usage class: {}\n".format(user.mode)
                 )

    return response


def prepare_help_message():
    """
    Prepare response to the "help" command
    @return: A text message
    """

    # command description used in the "help" command
    commands = {
        'hello': 'Get started with the the bot',
        'help': 'Gives you information about the available commands',
        'info': 'Return information about your usage',
        'me': 'Return information about your account'
    }

    # generate help text out of the commands dictionary defined at the top
    response = "The following commands are available: \n"
    for key in commands:
        response += "/" + key + ": "
        response += commands[key] + "\n"

    return response


def prepare_hello_message():
    """
    Prepare response to the "hello" command
    @return: A text message
    """

    response = _("bot.welcome")

    return response


@bot.message_handler(commands=['me'])
def command_me(message):
    """
    TelegramBot command "me"
    @param message:
    """

    text = message.text
    user_uuid = text.split()[1] if len(text.split()) > 1 else None
    if user_uuid:
        user = User.query.filter(User.uuid == f'{user_uuid}').first()

        bot.reply_to(message, prepare_me_info(user))
    else:
        bot.reply_to(message, "Please enter user_uuid")


@bot.message_handler(commands=['help'])
def command_help(message):
    """
    TelegramBot command "help"
    @param message:
    """

    bot.reply_to(message, prepare_help_message())


@bot.message_handler(commands=['hello'])
def command_hello(message):
    """
    TelegramBot command "hello"
    @param message:
    """

    bot.reply_to(message, prepare_hello_message())


@bot.message_handler(commands=['info'])
def command_info(message):
    """
    TelegramBot command "info"
    @param message:
    """
    print(message)
    text = message.text
    user_uuid = text.split()[1] if len(text.split()) > 1 else None
    print(user_uuid, text)
    if user_uuid:
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
    else:
        bot.reply_to(message, "Please enter user_uuid")
