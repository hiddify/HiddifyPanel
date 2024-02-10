from flask import jsonify, request
from apiflask import abort
from flask_restful import Resource
# from flask_simplelogin import login_required
import datetime
from hiddifypanel.models import *
from hiddifypanel.auth import login_required
from hiddifypanel.panel import hiddify
from hiddifypanel.drivers import user_driver


class UserResource(Resource):
    decorators = [login_required({Role.super_admin})]

    def get(self):
        uuid = request.args.get('uuid')
        if uuid:
            user = User.by_uuid(uuid) or abort(404, "user not found")
            return jsonify(user.to_dict())

        users = User.query.all() or abort(502, "WTF!")
        return jsonify([user.to_dict() for user in users])  # type: ignore

    def post(self):
        data = request.json
        uuid = data.get('uuid') or abort(422, "Parameter issue: 'uuid'")
        User.add_or_update(**data)  # type: ignore
        user = User.by_uuid(uuid) or abort(502, "unknown issue! user is not added")
        user_driver.add_client(user)
        hiddify.quick_apply_users()
        return jsonify({'status': 200, 'msg': 'ok'})

    def delete(self):
        uuid = request.args.get('uuid') or abort(422, "Parameter issue: 'uuid'")
        user = User.by_uuid(uuid) or abort(404, "user not found")
        user.remove()
        hiddify.quick_apply_users()
        return jsonify({'status': 200, 'msg': 'ok'})

        # start aliz dev
    # desc : it is better to have a delete method to manage users more programatically :)
    def delete(self, uuid=None):
        uuid = request.args['uuid'] if 'uuid' in request.args else None
        if uuid:
            user = User.query.filter(User.uuid == uuid).first() or abort(204)
            if user is not None:
                User.remove_user(uuid)
                # user_driver.remove_client(uuid)
                hiddify.quick_apply_users()
                return jsonify({'status': 200, 'msg': 'ok'})
            else:
                return jsonify({'status': 204, 'msg': 'user not found'})
        else:
            return jsonify({'status': 204, 'msg': 'uuid not found'})
    # end aliz dev


class AdminUserResource(Resource):
    decorators = [login_required({Role.super_admin})]

    def get(self, uuid=None):
        uuid = request.args.get('uuid')
        if uuid:
            admin = AdminUser.by_uuid(uuid) or abort(404, "user not found")
            return jsonify(admin.to_dict())

        admins = AdminUser.query.all() or abort(502, "WTF!")
        return jsonify([admin.to_dict() for admin in admins])

    def post(self):
        data = request.json
        uuid = data.get('uuid') or abort(422, "Parameter issue: 'uuid'")
        AdminUser.add_or_update(**data)  # type: ignore

        return jsonify({'status': 200, 'msg': 'ok'})

    def delete(self):
        uuid = request.args.get('uuid') or abort(422, "Parameter issue: 'uuid'")
        admin = AdminUser.by_uuid(uuid) or abort(404, "admin not found")
        admin.remove()
        return jsonify({'status': 200, 'msg': 'ok'})


# class DomainResource(Resource):
#     def get(self,domain=None):
#         if domain:
#             product = Domain.query.filter(Domain.domain==domain).first() or abort(204)
#             return jsonify(hiddify.domain_dict(product))
#         products = Domain.query.all() or abort(204)
#         return jsonify(
#             [hiddify.domain_dict(product) for product in products]
#         )
#     def post(self):
#         hiddify.add_or_update_domain(**request.json)
#         return jsonify({'status':200,'msg':'ok'})

# class ParentDomainResource(Resource):
#     def get(self,parent_domain=None):
#         if domain:
#             product = ParentDomain.query.filter(ParentDomain.domain==domain).first() or abort(204)
#             return jsonify(hiddify.parent_domain_dict(product))
#         products = ParentDomain.query.all() or abort(204)
#         return jsonify(
#             [hiddify.parent_domain_dict(product) for product in products]
#         )
#     def post(self):
#         hiddify.add_or_update_parent_domain(**request.json)
#         return jsonify({'status':200,'msg':'ok'})

# class ConfigResource(Resource):
#     def get(self,key=None,child_id=0):
#         if key:
#             return jsonify(hconfig(key,child_id))
#         return jsonify(get_hconfigs(child_id))

#     def post(self):
#         hiddify.add_or_update_config(**request.json)
#         return jsonify({'status':200,'msg':'ok'})

class HelloResource(Resource):
    def get(self):
        return jsonify({"status": 200, "msg": "ok"})


# class UpdateUsageResource(Resource):
#     def get(self):
#         return jsonify({"status": 200, "msg": "ok"})
