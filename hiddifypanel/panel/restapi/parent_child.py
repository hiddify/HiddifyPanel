from flask import abort, jsonify,request
from flask_restful import Resource
# from flask_simplelogin import login_required
import datetime
from hiddifypanel.models import StrConfig,BoolConfig,User,Domain,get_hconfigs,Proxy
from urllib.parse import urlparse
from hiddifypanel.panel import hiddify
class SyncChildResource(Resource):
     def put(self, panel_data):
        child_ip=request.remote_addr
        first_setup=False
        child=Child.query.filter(Child.ip==child_ip).first()
        if not child:
            first_setup=True
            child=Child(ip=child_ip)
            db.session.bulk_save_objects([child])
            db.session.commit()
            child=Child.query.filter(Child.ip==child_ip).first()
        
        hiddify.set_db_from_json(json_data,override_child=True,override_child_id=child.child_id,set_users=first_setup,remove_domains=True)

        return {"result":"ok"}


class AddUsageResource(Resource):
     def put(self, uuids_bytes):
        add_users_usage_uuid(uuids_bytes)
        return {"users": [u.to_dict() for u in User.query.all()]}

            

            
