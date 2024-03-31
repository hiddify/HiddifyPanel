from flask.views import MethodView
from flask import current_app as app

from hiddifypanel.auth import login_required
from hiddifypanel.models import Role
from hiddifypanel import __version__

from .schema import PanelInfoOutputSchema


class PanelInfoApi(MethodView):
    decorators = [login_required(roles={Role.super_admin, Role.admin, Role.agent}, node_auth=True)]

    @app.output(PanelInfoOutputSchema)  # type: ignore
    def get(self):
        res = PanelInfoOutputSchema()
        res.version = __version__  # type: ignore
        return res
