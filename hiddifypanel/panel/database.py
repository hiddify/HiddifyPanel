from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import UUIDType
from flask_migrate import Migrate,init,upgrade,migrate
import os

db = SQLAlchemy()
db.UUID = UUIDType


def init_app(app):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    db.init_app(app)

    # db.create_all(app)
    # app.jinja_env.globals['get_locale'] = get_locale
def init_migration(app):
    migrate = Migrate(app,db)
    if os.path.isdir(migrate.directory):
        return
    init()
