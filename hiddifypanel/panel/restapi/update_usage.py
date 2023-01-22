import xtlsapi
from flask import abort, jsonify
from flask_restful import Resource
from xtlsapi import XrayClient, utils, exceptions
from hiddifypanel.panel.database import db
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,hconfig
from hiddifypanel import xray_api
import datetime
class UpdateUsageResource(Resource):
    def get(self):
        to_gig_d = 1024*1024*1024
        res={}
        for user in db.session.query(User).all():
            if (datetime.today()-last_rest_time).days>=30:
                user.last_rest_time=datetime.today()
                if user.current_usage_GB > user.monthly_usage_limit_GB:
                    xray_api.add_client(user.uuid)
                user.current_usage_GB=0

            d = xray_api.get_usage(user.uuid)
            
            if d == None:
               res[user.uuid]="No value" 
            else:
                in_gig=(d)/to_gig_d
                res[user.uuid]=in_gig
                user.current_usage_GB += in_gig
            if user.current_usage_GB > user.monthly_usage_limit_GB:
                xray_api.remove_client(user.uuid)
                res[user.uuid]+=" !OUT of USAGE! Client Removed"
                    
        db.session.commit()
        
        return jsonify(
            {"status": 'success', "comments":res}
        )
