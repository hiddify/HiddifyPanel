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
# telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot("5845052699:AAElE7m_NWqempRmRBUmIPlV0yYmdQPtv1E",parse_mode="HTML",threaded=False)


def register_bot():
    # global bot
    # bot = telebot.TeleBot(hconfig(ConfigEnum.telegram_bot_token))
    bot.remove_webhook()
    import time

    time.sleep(0.1)

    domain=(ParentDomain if hconfig(ConfigEnum.is_parent) else Domain).query.first().domain
    bot.set_webhook(url=f"https://{domain}"+url_for("api.tgbotresource",proxy_path=hconfig(ConfigEnum.proxy_path), user_secret=hconfig(ConfigEnum.admin_secret)))

class TGBotResource(Resource):
    def get(self):
        register_bot()
        # domain=(ParentDomain if hconfig(ConfigEnum.is_parent) else Domain).query.first().domain
        return "ok "#+f"https://{domain}"+url_for("api.tgbotresource",proxy_path=hconfig(ConfigEnum.proxy_path), user_secret=hconfig(ConfigEnum.admin_secret))
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

def extract_uuid(text):
    # Extracts the uuid from the sent /start command.
    return text.split()[1] if len(text.split()) > 1 else None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # with force_locale(message.language_code):        
        text=message.text
        uuid=text.split()[1] if len(text.split()) > 1 else None
        print("start", uuid)
        if uuid:        
            # print("SSS")
            # print("msg=",get_usage_msg(uuid))
            # bot.reply_to(message,get_usage_msg(uuid))
            bot.reply_to(message,get_usage_msg(uuid),reply_markup=user_keyboard(uuid))
        else:
            bot.reply_to(message,_("Welcome to hiddifybot.\n Please click on the link in the panel page to start or enter your user uuid"))


@bot.message_handler(func=lambda message: True)
def not_handeled(message):
    print("hiiiiiiiiiiiiiii")
    bot.reply_to(message,"We can not understand your request")

def user_keyboard(uuid):
    return types.InlineKeyboardMarkup(
        keyboard=[
            [
                types.InlineKeyboardButton(
                    text="update",
                    callback_data="update_usage "+uuid
                )
            ]
        ]
    )
def get_usage_msg(uuid):
  with app.app_context():
    # print(request.base_url)
    user_data=get_common_data(uuid,'multi')
    user=user_data['user']
    expire_rel=user_data['expire_rel']
    # msg="D"
    msg=f"""{_('Welcome %(user)s',user=user.name if user.name!="default" else "")}\n"""
    msg+=f"""{_('user.home.usage.title')} {round(user.current_usage_GB,3)}GB <b>{_('user.home.usage.from')}</b> {user.usage_limit_GB}GB  {_('user.home.usage.monthly') if user.monthly else '' }\n
        <b>{_('user.home.usage.expire')}</b> {expire_rel}"""
    
    if user_data['reset_day']<500:
        msg+=f"""\n<b>{_('Reset Usage Time:')}</b> {reset_day} {_('days')}"""
    return msg


@bot.callback_query_handler(func=lambda call: call.data.startswith("update_usage"))
# @bot.callback_query_handler(func=lambda call: True)
def update_usage_callback(call): # <- passes a CallbackQuery type object to your function
    # with force_locale(message.language_code):
        print("\n\ncallid:",call.id)
        
        text=call.data
        uuid=text.split()[1] if len(text.split()) > 1 else None
        # print("uuid",uuid)
        if uuid:
            try:
                new_text=get_usage_msg(uuid)
                bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id,reply_markup=user_keyboard(uuid))
                bot.answer_callback_query(call.id, text='Updated', show_alert=False,cache_time =1)
            except Exception as e:
                print (e)
                bot.answer_callback_query(call.id,cache_time =1)
            # bot.edit_message_text("D", call.message.chat.id, call.message.message_id,reply_markup=user_keyboard(uuid))
        # bot.answer_callback_query(callback_query_id=call.id, text='Updated', show_alert=False)
        # bot.answer_callback_query(callback_query_id=call.id, text='Updated', show_alert=False)
        
# bot.infinity_polling()
