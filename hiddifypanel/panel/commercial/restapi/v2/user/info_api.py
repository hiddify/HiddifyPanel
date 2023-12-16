from urllib.parse import urlparse
from flask.views import MethodView
from apiflask import Schema
from apiflask.fields import Integer, String, Float, URL, Enum
from flask import g, request
from flask import current_app as app

from hiddifypanel.models import Lang
from hiddifypanel.models.user import days_to_reset, get_user_by_uuid
from hiddifypanel.models.config import hconfig
from hiddifypanel.models.config_enum import ConfigEnum
from hiddifypanel.panel import hiddify
from hiddifypanel.panel.database import db
from hiddifypanel.panel.user.user import get_common_data
from hiddifypanel.panel.authentication import api_auth


class ProfileSchema(Schema):
    profile_title = String(required=True)
    profile_url = URL(required=True)
    profile_usage_current = Float(required=True)
    profile_usage_total = Float(required=True)
    profile_remaining_days = Integer(required=True)
    profile_reset_days = Integer()
    telegram_bot_url = String()
    telegram_id = Integer()
    admin_message_html = String()
    admin_message_url = URL()
    brand_title = String()
    brand_icon_url = URL()
    doh = URL()
    lang = Enum(Lang, required=True)


class UserInfoChangableSchema(Schema):
    language = Enum(Lang, required=False)
    telegram_id = Integer(required=False)


class InfoAPI(MethodView):
    decorators = [hiddify.user_auth]

    @app.output(ProfileSchema)
    def get(self):
        c = get_common_data(g.account_uuid, 'new')

        dto = ProfileSchema()
        # user is exist for sure
        dto.profile_title = c['user'].name
        dto.profile_url = f"https://{urlparse(request.base_url).hostname}/{g.proxy_path}/{g.account_uuid}/#{g.account.name}"
        dto.profile_usage_current = g.account.current_usage_GB
        dto.profile_usage_total = g.account.usage_limit_GB
        dto.profile_remaining_days = g.account.remaining_days
        dto.profile_reset_days = days_to_reset(g.account)
        dto.telegram_bot_url = f"https://t.me/{c['bot'].username}?start={g.account_uuid}" if c['bot'] else ""
        dto.telegram_id = c['user'].telegram_id
        dto.admin_message_html = hconfig(ConfigEnum.branding_freetext)
        dto.admin_message_url = hconfig(ConfigEnum.branding_site)
        dto.brand_title = hconfig(ConfigEnum.branding_title)
        dto.brand_icon_url = ""
        dto.doh = f"https://{urlparse(request.base_url).hostname}/{g.proxy_path}/dns/dns-query"
        dto.lang = c['user'].lang
        return dto

    @app.input(UserInfoChangableSchema, arg_name='data')
    def patch(self, data):
        if data['telegram_id']:
            try:
                tg_id = int(data['telegram_id'])
            except:
                return {'message': 'The telegram id field is invalid'}

            user = get_user_by_uuid(g.account_uuid)
            if user.telegram_id != tg_id:
                user.telegram_id = tg_id
                db.session.commit()

        if data['language']:
            user = get_user_by_uuid(g.account_uuid)
            if user.lang != data['language']:
                user.lang = data['language']
                db.session.commit()
        return {'message': 'ok'}
