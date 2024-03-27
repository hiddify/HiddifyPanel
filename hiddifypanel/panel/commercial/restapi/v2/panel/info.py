from flask.views import MethodView
from apiflask import Schema, fields
from flask import current_app as app

from hiddifypanel.auth import login_required
from hiddifypanel.models import Role
from hiddifypanel import __version__


class PanelInfoOutputSchema(Schema):
    version = fields.String(description="The panel version")


class PanelInfoApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin, Role.agent})]

    @app.output(PanelInfoOutputSchema)  # type: ignore
    def get(self):
        res = PanelInfoOutputSchema()
        res.version = __version__  # type: ignore
        return res
