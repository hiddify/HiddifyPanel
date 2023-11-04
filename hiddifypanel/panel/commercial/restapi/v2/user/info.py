from flask_restful import Resource
from hiddifypanel.panel import hiddify

from flask_classful import FlaskView, route
from flask.views import MethodView

from flask import current_app as app
from apiflask import APIFlask, Schema, abort
from apiflask.fields import Integer, String
from apiflask.validators import Length, OneOf


class PetIn(Schema):
    name = String(required=True, validate=Length(0, 10))
    category = String(required=True, validate=OneOf(['dog', 'cat']))


class PetOut(Schema):
    id = Integer()
    name = String()
    category = String()


class Info(MethodView):
    decorators = [hiddify.user_auth]
    @app.output(PetOut)
    def get(self):
        abort(404)
        pass

    @app.input(PetIn(partial=True))
    @app.output(PetOut)
    def post(self):
        pass
