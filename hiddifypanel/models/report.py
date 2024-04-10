import datetime


from hiddifypanel.database import db
from sqlalchemy_serializer import SerializerMixin


class Report(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), default=0, nullable=False)
    asn_id = db.Column(db.String(200), nullable=False, unique=False)
    city = db.Column(db.String(200))
    country = db.Column(db.String(200))
    latitude = Column(Float,)
    longitude = Column(Float, )
    accuracy_radius = Column(Float, )

    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.min)
    details = db.relationship('ReportDetail', cascade="all,delete", backref='report', lazy='dynamic',)


class ReportDetail(db.Model, SerializerMixin):
    report_id = db.Column(db.Integer, db.ForeignKey('report.id'), primary_key=True, )
    proxy_id = db.Column(db.Integer, db.ForeignKey('proxy.id'), primary_key=True, )
    ping = db.Column(db.Integer, default=-1)
