import xtlsapi
from flask import abort, jsonify
from flask_restful import Resource
from xtlsapi import XrayClient, utils, exceptions
from hiddifypanel.panel.database import db
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,hconfig
from hiddifypanel import xray_api
from hiddifypanel.panel import hiddify
import datetime
class UpdateUsageResource(Resource):
    def get(self):
        return jsonify(hiddify.update_usage())
