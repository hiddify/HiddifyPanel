from sqlalchemy_serializer import SerializerMixin

from hiddifypanel.panel.database import db


class Child(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # ip = db.Column(db.String(200), nullable=False, unique=True)
    unique_id = db.Column(db.String(200), nullable=False, unique=True)
    domains = db.relationship('Domain', cascade="all,delete", backref='child')
    proxies = db.relationship('Proxy', cascade="all,delete", backref='child')
    boolconfigs = db.relationship('BoolConfig', cascade="all,delete", backref='child')
    strconfigs = db.relationship('StrConfig', cascade="all,delete", backref='child')
    dailyusages = db.relationship('DailyUsage', cascade="all,delete", backref='child')
