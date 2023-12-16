
from apiflask.fields import Integer, String, UUID, Boolean, Enum
from flask import current_app as app
from flask.views import MethodView
from apiflask import Schema
from apiflask import abort


from hiddifypanel.models import *
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
from hiddifypanel.models import AdminMode, Lang
from hiddifypanel.panel.authentication import api_auth


class AdminSchema(Schema):
    name = String(required=True, description='The name of the admin')
    comment = String(required=False, description='A comment related to the admin')
    uuid = UUID(required=True, description='The unique identifier for the admin')
    mode = Enum(AdminMode, required=True, description='The mode for the admin')
    can_add_admin = Boolean(required=True, description='Whether the admin can add other admins')
    parent_admin_uuid = UUID(description='The unique identifier for the parent admin', allow_none=True,
                             # validate=OneOf([p.uuid for p in AdminUser.query.all()])
                             )
    telegram_id = Integer(required=True, description='The Telegram ID associated with the admin')
    lang = Enum(Lang, required=True)


class AdminUserApi(MethodView):
    decorators = [hiddify.admin]

    @app.output(AdminSchema)
    def get(self, uuid):

        admin = get_admin_user_db(uuid) or abort(404, "user not found")
        return admin.to_dict()

    @app.input(AdminSchema, arg_name='data')
    def patch(self, uuid, data):
        data['uuid'] = uuid
        hiddify.add_or_update_admin(**data)
        return {'status': 200, 'msg': 'ok'}

    def delete(self, uuid):
        admin = get_admin_user_db(uuid) or abort(404, "admin not found")
        admin.remove()
        return {'status': 200, 'msg': 'ok'}
