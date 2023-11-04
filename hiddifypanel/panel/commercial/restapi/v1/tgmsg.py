from flask import abort, jsonify, request
from flask_restful import Resource
# from flask_simplelogin import login_required
import datetime
from hiddifypanel.panel.database import db
from hiddifypanel.models import *
from urllib.parse import urlparse
from hiddifypanel.panel import hiddify, usage
from .tgbot import bot


class SendMsgResource(Resource):
    def post(self):

        if not hconfig(ConfigEnum.telegram_bot_token):
            abort(400)

        msg = request.json
        users = User.query.filter(User.telegram_id != None)
        id = msg['id']
        if type(id) == int or id.isnumeric():
            users = [users.filter(User.id == int(msg['id'])).first() or abort(403)]
        elif id == 'all':
            users = users.all()
        else:
            users = users.all()
            if id == 'expired':
                users = [u for u in users if not is_user_active(u)]
            elif id == 'active':
                users = [u for u in users if is_user_active(u)]
            elif id == 'offline 1h':
                h1 = datetime.datetime.now()-datetime.timedelta(hours=1)
                users = [u for u in users if is_user_active(u) and u.last_online < h1]
            elif id == 'offline 1d':
                d1 = datetime.datetime.now()-datetime.timedelta(hours=24)
                users = [u for u in users if is_user_active(u) and u.last_online < d1]

            elif id == 'offline 1w':
                d7 = datetime.datetime.now()-datetime.timedelta(days=7)
                users = [u for u in users if is_user_active(u) and u.last_online < d7]

        res = {}
        for user in users:
            try:
                from hiddifypanel.panel.commercial.telegrambot import Usage
                keyboard = Usage.user_keyboard(user.uuid)
                txt = msg['text']+"\n\n"+Usage.get_usage_msg(user.uuid)
                print('sending to ', user)
                bot.send_message(user.telegram_id, txt, reply_markup=keyboard)
            except Exception as e:
                import traceback
                res[user.uuid] = {'name': user.name, 'error': f'{e}'}
        if len(res) == 0:
            return {'msg': "success"}
        else:
            return {'msg': 'error', 'res': res}
