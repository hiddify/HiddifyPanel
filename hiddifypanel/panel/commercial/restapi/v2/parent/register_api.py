from apiflask import abort
from hiddifypanel.database import db
from flask import current_app as app
from flask.views import MethodView

from hiddifypanel.models import *
from hiddifypanel.auth import login_required

from .schema import RegisterInputSchema, RegisterOutputSchema


class RegisterApi(MethodView):
    decorators = [login_required({Role.super_admin})]

    @app.input(RegisterInputSchema, arg_name='data')  # type: ignore
    @app.output(RegisterOutputSchema)  # type: ignore
    def put(self, data):
        from hiddifypanel import hutils
        if hutils.node.is_child():
            abort(400, 'The panel in child, not a parent nor standalone')

        unique_id = data['unique_id']
        name = data['name']
        mode = data['mode']

        child = Child.query.filter(Child.unique_id == unique_id).first()
        if not child:
            child = Child(unique_id=unique_id, name=name, mode=mode)
            db.session.add(child)  # type: ignore
            db.session.commit()  # type: ignore
            child = Child.query.filter(Child.unique_id == unique_id).first()

        try:
            # add data
            AdminUser.bulk_register(data['panel_data']['admin_users'], commit=False)
            User.bulk_register(data['panel_data']['users'], commit=False)
            bulk_register_domains(data['panel_data']['domains'], commit=False, force_child_unique_id=child.unique_id)
            bulk_register_configs(data['panel_data']['hconfigs'], commit=False, froce_child_unique_id=child.unique_id)
            Proxy.bulk_register(data['panel_data']['proxies'], commit=False, force_child_unique_id=child.unique_id)
            db.session.commit()  # type: ignore
        except Exception as err:
            abort(400, str(err))

        if not hutils.node.is_parent():
            set_hconfig(ConfigEnum.panel_mode, PanelMode.parent)  # type: ignore

        res = RegisterOutputSchema()
        res.users = [u.to_schema() for u in User.query.all()]  # type: ignore
        res.admin_users = [a.to_schema() for a in AdminUser.query.all()]  # type: ignore
        res.parent_unique_id = hconfig(ConfigEnum.unique_id)

        return res
