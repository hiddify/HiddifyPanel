from flask.views import MethodView

from hiddifypanel.auth import login_required
from hiddifypanel.models import Role


class PingPongApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin, Role.agent})]

    def get(self):
        return {'msg': 'GET: PONG'}

    def post(self):
        return {'msg': 'POST: PONG'}

    def patch(self):
        return {'msg': 'PATCH: PONG'}

    def delete(self):
        return {'msg': 'DELETE: PONG'}

    def put(self):
        return {'msg': 'PUT: PONG'}
