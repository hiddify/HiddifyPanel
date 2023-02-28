from flask import abort, jsonify,request
from flask_restful import Resource
# from flask_simplelogin import login_required
import datetime
from hiddifypanel.models import *
from urllib.parse import urlparse
from hiddifypanel.panel import hiddify,hiddify_api
class AllResource(Resource):
    def get(self):
        products = User.query.all() or abort(204)
        response= jsonify(
            hiddify.dump_db_to_dict()            
        )
        o = urlparse(request.base_url)
        domain=o.hostname
        response.headers.add('Content-disposition', f'attachment; filename=hiddify-{domain}-{datetime.datetime.now()}.json');

        return response



class UserResource(Resource):
    def get(self,uuid=None):
        if uuid:
            product = User.query.filter(User.uuid==uuid).first() or abort(204)
            return jsonify(product.to_dict())    

        products = User.query.all() or abort(204)
        return jsonify(
            [product.to_dict() for product in products]
        )

    def post(self):
        hiddify.add_or_update_user(**request.json)
        return jsonify({'status':200,'msg':'ok'})


class DomainResource(Resource):
    def get(self,domain=None):
        if domain:
            product = Domain.query.filter(Domain.domain==domain).first() or abort(204)
            return jsonify(hiddify.domain_dict(product))    
        products = Domain.query.all() or abort(204)
        return jsonify(
            [hiddify.domain_dict(product) for product in products]
        )
    def post(self):
        hiddify.add_or_update_domain(**request.json)
        return jsonify({'status':200,'msg':'ok'})

class ParentDomainResource(Resource):
    def get(self,parent_domain=None):
        if domain:
            product = ParentDomain.query.filter(ParentDomain.domain==domain).first() or abort(204)
            return jsonify(hiddify.parent_domain_dict(product))    
        products = ParentDomain.query.all() or abort(204)
        return jsonify(
            [hiddify.parent_domain_dict(product) for product in products]
        )
    def post(self):
        hiddify.add_or_update_parent_domain(**request.json)
        return jsonify({'status':200,'msg':'ok'})

class ConfigResource(Resource):
    def get(self,key=None,child_id=0):
        if key:
            return jsonify(hconfig(key,child_id))
        return jsonify(get_hconfigs(child_id))

    def post(self):
        hiddify.add_or_update_config(**request.json)
        return jsonify({'status':200,'msg':'ok'})

class HelloResource(Resource):
    def get(self):
        return jsonify({"status": 200,"msg":"ok"})


