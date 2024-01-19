from typing import List
from flask import g, request
from apiflask import abort
from flask_restful import Resource
# from flask_simplelogin import login_required
import datetime

from hiddifypanel import hutils
from hiddifypanel.models import *
from .tgbot import bot


class SendMsgResource(Resource):
    # decorators = [login_required({Role.super_admin})]
    def post(self, admin_uuid=None):

        if not hconfig(ConfigEnum.telegram_bot_token) or not bot:
            abort(400, 'invalid request')

        msg = request.json
        if not msg or not msg.get('id') or not msg.get('text'):
            abort(400, 'invalid request')

        users = self.get_users_by_identifier(msg['id'])

        res = {}
        for user in users:
            try:
                from hiddifypanel.panel.commercial.telegrambot import Usage
                keyboard = Usage.user_keyboard(user.uuid)
                txt = msg['text']+"\n\n"+Usage.get_usage_msg(user.uuid)
                print('sending to ', user)
                bot.send_message(user.telegram_id, txt, reply_markup=keyboard)
            except Exception as e:
                res[user.uuid] = {'name': user.name, 'error': f'{e}'}
        if len(res) == 0:
            return {'msg': "success"}
        else:
            return {'msg': 'error', 'res': res}

    def get_users_by_identifier(self, identifier: str) -> List[User]:
        '''Returns all users that match the identifier for sending a message to them'''
        # when we are here we must have g.account but ...
        if not hasattr(g, 'account'):
            return []
        query = User.query.filter(User.added_by.in_(g.account.recursive_sub_admins_ids()))
        query = query.filter(User.telegram_id != None, User.telegram_id != 0)

        if hutils.utils.is_int(identifier):
            return [query.filter(User.id == int(identifier)).first() or abort(404, 'The user not found')]  # type: ignore
        elif identifier == 'all':
            return query.all()
        elif identifier == 'expired':
            return [u for u in query.all() if not u.is_active]
        elif identifier == 'active':
            return [u for u in query.all() if u.is_active]
        elif identifier == 'offline 1h':
            h1 = datetime.datetime.now()-datetime.timedelta(hours=1)
            return [u for u in query.all() if u.is_active and u.last_online < h1]
        elif identifier == 'offline 1d':
            d1 = datetime.datetime.now()-datetime.timedelta(hours=24)
            return [u for u in query.all() if u.is_active and u.last_online < d1]
        elif identifier == 'offline 1w':
            d7 = datetime.datetime.now()-datetime.timedelta(days=7)
            return [u for u in query.all() if u.is_active and u.last_online < d7]
        else:
            return []
