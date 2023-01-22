import xtlsapi
from flask import abort, jsonify
from flask_restful import Resource
from xtlsapi import XrayClient, utils, exceptions
from hiddifypanel.panel.database import db
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,hconfig
import datetime
class UpdateUsageResource(Resource):
    def get(self):
        
        to_gig_d = 1024*1024*1024
        xray_client = XrayClient('127.0.0.1', 10085)
        res={}
        for user in db.session.query(User).all():
            if (datetime.today()-last_rest_time).days>=30:
                user.last_rest_time=datetime.today()
                user.current_usage_GB=0

            d = xray_client.get_client_download_traffic(f'{user.uuid}@hiddify.com')
            u = xray_client.get_client_upload_traffic(f'{user.uuid}@hiddify.com')
            if d == None or u == None:
               res[user.uuid]="No value" 
            else:
                in_gig=(d+u)/to_gig_d
                res[user.uuid]=in_gig
                user.current_usage_GB += in_gig
        db.session.commit()

        return jsonify(
            {"status": 'success', "comments":res}
        )
