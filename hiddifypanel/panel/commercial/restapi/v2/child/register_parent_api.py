from apiflask import abort, fields, Schema
from flask.views import MethodView
from flask import current_app as app, g
from flask_babel import lazy_gettext as _

from hiddifypanel.auth import login_required
from hiddifypanel.models import set_hconfig, ConfigEnum, PanelMode, ChildMode, Role
from hiddifypanel import hutils


class RegisterWithParentInputSchema(Schema):
    parent_unique_id = fields.String(description="The parent's unique id")
    parent_panel = fields.String(required=True, description="The parent panel url")
    name = fields.String(required=True, description="The child's name in the parent panel")


class RegisterWithParentApi(MethodView):
    decorators = [login_required({Role.super_admin})]

    @app.input(RegisterWithParentInputSchema, arg_name='data')  # type: ignore
    def post(self, data):
        if hutils.node.is_parent() or hutils.node.is_child():
            abort(400, 'The panel is not in standalone mode')
        set_hconfig(ConfigEnum.parent_panel, data['parent_panel'])  # type: ignore
        set_hconfig(ConfigEnum.parent_unique_id, data['parent_unique_id'])  # type: ignore

        if not hutils.node.child.register_to_parent(data['name']):
            abort(400, _('child.register-failed'))  # type: ignore

        set_hconfig(ConfigEnum.panel_mode, PanelMode.child)  # type: ignore
        return {'status': 200, 'msg': 'ok'}
