import xtlsapi
from flask_restful import Resource
from xtlsapi import XrayClient, utils, exceptions
from hiddifypanel.panel.database import db


class UpdateResource(Resource):
    def get(self):
        to_gig_d = 1024*1024*1024
        xray_client = XrayClient('127.0.0.1', 10085)
        for user in db.session.query(User).all():
            d = xtlsapi.get_client_download_traffic(f'{user.uuid}@hiddify.com')
            u = xtlsapi.get_client_upload_traffic(f'{user.uuid}@hiddify.com')
            user.current_usage_GB += (d+u)/to_gig_d
        db.session.commit()

        return jsonify(
            {"status": 'success'}
        )
