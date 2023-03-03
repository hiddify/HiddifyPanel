from hiddifypanel.models import *
import telebot
from telebot import types, TeleBot
import logging
from flask_babelex import gettext as _
from flask_babel import force_locale

from flask import abort, jsonify,request,url_for
from flask import current_app as app
from flask_restful import Resource
# from flask_simplelogin import login_required
import datetime
from hiddifypanel.models import *
from hiddifypanel.panel.user.user import get_common_data
from urllib.parse import urlparse
from hiddifypanel.panel import hiddify,hiddify_api
logger = telebot.logger

class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        logger.error(exception)



# telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot("",parse_mode="HTML",threaded=False,exception_handler=ExceptionHandler())


def register_bot():
    global bot
    token=hconfig(ConfigEnum.telegram_bot_token)
    if token:
        bot.token = hconfig(ConfigEnum.telegram_bot_token)
        bot.remove_webhook()
        import time
        time.sleep(0.1)
        domain=(ParentDomain if hconfig(ConfigEnum.is_parent) else Domain).query.first().domain
        proxy_path=hconfig(ConfigEnum.proxy_path)
        user_secret=hconfig(ConfigEnum.admin_secret)
        bot.set_webhook(url=f"https://{domain}/{proxy_path}/{user_secret}/api/v1/tgbot/")

import hiddifypanel.panel.telegrambot
class TGBotResource(Resource):
    # def get(self):
    #     register_bot()
    #     # domain=(ParentDomain if hconfig(ConfigEnum.is_parent) else Domain).query.first().domain
    #     return "ok "#+f"https://{domain}"+url_for("api.tgbotresource",proxy_path=hconfig(ConfigEnum.proxy_path), user_secret=hconfig(ConfigEnum.admin_secret))
    def post(self):
        try:
            if request.headers.get('content-type') == 'application/json':
            
                json_string = request.get_data().decode('utf-8')
                
                # print(json_string)
                update = telebot.types.Update.de_json(json_string)
                bot.process_new_updates([update])
                return ''
            else:
                abort(403)
        except Exception as e:
            print("Error",e)
            import traceback
            traceback.print_exc()
            return "",500


