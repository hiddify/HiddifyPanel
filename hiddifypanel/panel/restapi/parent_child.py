from flask import abort, jsonify,request
from flask_restful import Resource
# from flask_simplelogin import login_required
import datetime
from hiddifypanel.panel.database import db
from hiddifypanel.models import *
from urllib.parse import urlparse
from hiddifypanel.panel import hiddify
class SyncChildResource(Resource):
    def get(self):
        if not hconfig(ConfigEnum.is_parent):
            return {'status':500,'msg':"Not a parent"},500
        return 

    def put(self):
     try:
        panel_data=request.json
        if not hconfig(ConfigEnum.is_parent):
            raise Exception("Not a parent")
        print(request.headers)
        unique_id=request.headers['Unique-Id']
        print(panel_data)
        print("==================")
        
        first_setup=False
        
        child=Child.query.filter(Child.unique_id==unique_id).first()
        if not child:
            first_setup=True
            child=Child(unique_id=unique_id)
            db.session.add(child)
            db.session.commit()
            child=Child.query.filter(Child.unique_id==unique_id).first()
        
        hiddify.set_db_from_json(panel_data,override_child_id=child.id,set_users=first_setup,remove_domains=True)

        return {'status':200,"msg":"ok"}
     except Exception as e:
            print(e)
            return {'status':500,"msg":str(e)},500

class AddUsageResource(Resource):
     def put(self):
        uuids_bytes=request.json
        add_users_usage_uuid(uuids_bytes)
        return {"users": [u.to_dict() for u in User.query.all()]}

            

            
