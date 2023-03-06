from . import bot
from hiddifypanel.models import *
from telebot import types
from flask_babelex import gettext as _
from flask import abort, jsonify,request,url_for
from flask import current_app as app
from hiddifypanel.panel.user.user import get_common_data
from . import admin
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # with force_locale(message.language_code):        
        text=message.text
        uuid=text.split()[1] if len(text.split()) > 1 else None
        print("start", uuid)
        if uuid: 
            if uuid==hconfig(ConfigEnum.admin_secret):
                admin.start_admin(message)
                return
            # print("SSS")
            # print("msg=",get_usage_msg(uuid))
            # bot.reply_to(message,get_usage_msg(uuid))
            bot.reply_to(message,get_usage_msg(uuid),reply_markup=user_keyboard(uuid))
        else:
            bot.reply_to(message,_("Welcome to hiddifybot.\n Please click on the link in the panel page to start or enter your user uuid"))
            # uuid=User.query.first().uuid
            # bot.reply_to(message,f"Demo: enter <pre>/start {uuid}</pre>")



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
    reset_day=user_data['reset_day']
    # msg="D"
    msg=f"""{_('Welcome %(user)s',user=user.name if user.name!="default" else "")}\n"""
    msg+=f"""{_('user.home.usage.title')} {round(user.current_usage_GB,3)}GB <b>{_('user.home.usage.from')}</b> {user.usage_limit_GB}GB  {_('user.home.usage.monthly') if user.monthly else '' }\n
        <b>{_('user.home.usage.expire')}</b> {expire_rel}"""
    
    if reset_day<500:
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
