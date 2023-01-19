from flask import abort, jsonify
from flask_restful import Resource
from flask_simplelogin import login_required
import datetime
from hiddifypanel.models import StrConfig,BoolConfig,User,Domain,get_hconfigs


class AllResource(Resource):
    def get(self):
        products = User.query.all() or abort(204)
        return jsonify(
            {"users": [u.to_dict() for u in User.query.filter((User.monthly_usage_limit_GB>User.current_usage_GB)).filter(User.expiry_time>=datetime.date.today()).all()],
            "domains": [u.to_dict() for u in Domain.query.all()],
            "hconfigs": get_hconfigs()
            }
        )


class UserResource(Resource):
    def get(self):
        products = User.query.all() or abort(204)
        return jsonify(
            {"users": [product.to_dict() for product in products]}
        )

class DomainResource(Resource):
    def get(self):
        products = Domain.query.all() or abort(204)
        return jsonify(
            {"domains": [product.to_dict() for product in products]}
        )

class BoolConfigResource(Resource):
    def get(self):
        products = BoolConfig.query.all() or abort(204)
        return jsonify(
            {"bool_configs": [product.to_dict() for product in products]}
        )

class StrConfigResource(Resource):
    def get(self):
        products = StrConfig.query.all() or abort(204)
        return jsonify(
            {"str_configs": [product.to_dict() for product in products]}
        )
