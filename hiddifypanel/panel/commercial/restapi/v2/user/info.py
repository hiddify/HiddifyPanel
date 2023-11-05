from flask_restful import Resource
from hiddifypanel.panel import hiddify

from flask_classful import FlaskView, route
from flask.views import MethodView

from flask import current_app as app
from apiflask import APIFlask, Schema, abort
from apiflask.fields import Integer, String, Float, URL
from apiflask.validators import Length, OneOf


class ProfileDTO(Schema):
    profile_title = String(required=True)
    profile_url = URL(required=True)
    profile_usage_current = Float(required=True)
    profile_usage_total = Float(required=True)
    profile_remaining_days = Integer(required=True)
    profile_reset_days = Integer()
    telegram_bot_url = String()
    admin_message_html = String()
    admin_message_url = URL()
    brand_title = String()
    brand_icon_url = URL()
    doh = URL()
    def_lang = String(validate=OneOf(['en', 'fa', 'ru', 'pt', 'zh']))


class UserInfoChangableDTO(Schema):
    language = String(required=True, validate=OneOf(['en', 'fa', 'ru', 'pt', 'zh']))


class Info(MethodView):
    decorators = [hiddify.user_auth]

    @app.output(ProfileDTO)
    def get(self):
        return g.uuid
        # TODO use data from user panel page
        abort(404)
        pass

    @app.input(UserInfoChangableDTO)
    def post(self):
        # TODO add prefered language
        return {'message': 'ok'}
