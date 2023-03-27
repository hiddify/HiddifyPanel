from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import UUIDType


db = SQLAlchemy()
db.UUID=UUIDType

def init_app(app):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    db.init_app(app)

    # db.create_all(app)
    # app.jinja_env.globals['get_locale'] = get_locale





