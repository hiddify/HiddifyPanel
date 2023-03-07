import time
import telebot
from flask import abort, request
from flask_restful import Resource

from hiddifypanel.models import *

logger = telebot.logger


class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        logger.error(exception)


bot = telebot.TeleBot("", parse_mode="HTML", threaded=False, exception_handler=ExceptionHandler())


def register_bot():
    global bot
    token = hconfig(ConfigEnum.telegram_bot_token)
    if token:
        bot.token = hconfig(ConfigEnum.telegram_bot_token)
        bot.remove_webhook()
        time.sleep(0.1)
        domain = (ParentDomain if hconfig(ConfigEnum.is_parent) else Domain).query.first().domain
        proxy_path = hconfig(ConfigEnum.proxy_path)
        user_secret = hconfig(ConfigEnum.admin_secret)
        bot.set_webhook(url=f"https://{domain}/{proxy_path}/{user_secret}/api/v1/tgbot/")


class TGBotResource(Resource):
    def post(self):
        try:
            if request.headers.get('content-type') == 'application/json':
                json_string = request.get_data().decode('utf-8')
                update = telebot.types.Update.de_json(json_string)
                bot.process_new_updates([update])
                return ''
            else:
                abort(403)
        except Exception as e:
            print("Error", e)
            import traceback
            traceback.print_exc()
            return "", 500
