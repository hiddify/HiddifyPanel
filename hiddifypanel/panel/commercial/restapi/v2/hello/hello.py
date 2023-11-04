from flask_restful import Resource
from hiddifypanel.panel import hiddify

from flask_classful import FlaskView, route
from flask.views import MethodView

from flask import current_app as app
from apiflask import APIFlask, Schema, abort
from apiflask.fields import Integer, String
from apiflask.validators import Length, OneOf


class IDDTO(Schema):
    id = Integer()


class Hello(MethodView):

    def get(self):
        return {'message': 'hello get'}

    def post(self):
        return {'message': 'hello post'}

    def patch(self):
        return {'message': 'hello patch'}

    def delete(self):
        return {'message': f'hello delete'}

    def put(self):
        return {'message': 'hello put'}
