from urllib.parse import urlparse
from flask.views import MethodView
from apiflask import Schema
from apiflask.fields import Integer, String, Float, URL, Enum
from flask import g, request
from flask import current_app as app
from hiddifypanel.panel.auth import login_required
import hiddifypanel.panel.auth as auth
from flask_babelex import gettext as _
from hiddifypanel.models import Lang
from hiddifypanel.models.role import Role
from hiddifypanel.models.user import User
from hiddifypanel.models.config import hconfig
from hiddifypanel.models.config_enum import ConfigEnum
from hiddifypanel.panel.database import db
from hiddifypanel.panel.user.user import get_common_data


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
    decorators = [login_required({Role.user})]

    @app.output(ProfileSchema)
    def get(self):
        c = get_common_data(g.account.uuid, 'new')

        dto = ProfileSchema()
        # user is exist for sure
        dto.profile_title = c['user'].name
        dto.profile_url = c['profile_url']
        dto.profile_usage_current = g.account.current_usage_GB
        dto.profile_usage_total = g.account.usage_limit_GB
        dto.profile_remaining_days = g.account.remaining_days()
        dto.profile_reset_days = g.account.days_to_reset()
        dto.telegram_bot_url = f"https://t.me/{c['bot'].username}?start={g.account.uuid}" if c['bot'] else ""
        dto.telegram_id = c['user'].telegram_id or 0
        dto.admin_message_html = hconfig(ConfigEnum.branding_freetext) or _("Join our Hiddify Telegram channel to get the latest updates on Hiddify.")
        if not hconfig(ConfigEnum.branding_freetext) and auth.admin_session_is_exist():
            dto.admin_message_html += "<p style='font-style: italic;font-size:8px'>"+_("[Admin only visible message:] You can change this message from settings")+"</p>"
        dto.admin_message_url = hconfig(ConfigEnum.branding_site) or "https://t.me/hiddify"
        dto.brand_title = hconfig(ConfigEnum.branding_title) or _("Hiddify")
        dto.brand_icon_url = "" if hconfig(ConfigEnum.branding_title) else static_url_for(filename="images/hiddify.png")
        dto.doh = f"https://{request.host}/{g.proxy_path}/dns/dns-query"
        dto.lang = c['user'].lang
        return dto

    @app.input(UserInfoChangableSchema, arg_name='data')
    def patch(self, data):
        if data['telegram_id']:
            try:
                tg_id = int(data['telegram_id'])
            except:
                return {'message': 'The telegram id field is invalid'}

            user = User.by_uuid(g.account.uuid)
            if user.telegram_id != tg_id:
                user.telegram_id = tg_id
                db.session.commit()

        if data['language']:
            user = User.by_uuid(g.account.uuid)
            if user.lang != data['language']:
                user.lang = data['language']
                db.session.commit()
        return {'message': 'ok'}
