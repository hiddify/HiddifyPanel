from flask import abort, jsonify,request
from flask_restful import Resource
# from flask_simplelogin import login_required
import datetime
from hiddifypanel.panel.database import db
from hiddifypanel.models import *
from urllib.parse import urlparse
from hiddifypanel.panel import hiddify,usage
from .tgbot import bot
class SendMsgResource(Resource):
     def post(self):
        
        if not hconfig(ConfigEnum.telegram_bot_token):
            abort(400)
        print("fuck",request)
        print("fuck",request.json)
        msg=request.json
        print(msg)
        user=User.query.filter(User.id==int(msg['id'])).first() or abort(403)
        if not user.telegram_id:
            abort(403)
        
        bot.send_message(user.telegram_id, msg['text'])
        return "success"

            

            
