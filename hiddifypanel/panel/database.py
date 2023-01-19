from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import UUIDType

db = SQLAlchemy()
db.UUID=UUIDType

def init_app(app):
    db.init_app(app)
