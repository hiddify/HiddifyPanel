from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import UUIDType
# import flask_migrate
# from flask_migrate import upgrade
import re
import os

db = SQLAlchemy()
db.UUID = UUIDType

def init_app(app):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    db.init_app(app)

    # db.create_all(app)
    # app.jinja_env.globals['get_locale'] = get_locale
def init_migration(app):
    migrate = flask_migrate.Migrate(app,db)
    if os.path.isdir(migrate.directory):
        return
    flask_migrate.init()
def migrate():
    try_again = False
    try:
        # run flask_migrate.migrate function without its decorator to catch function error in try statement
        flask_migrate.migrate.__wrapped__()
    except Exception as err:
        err_str = str(err)
        if err_str == 'Target database is not up to date.':
            flask_migrate.stamp()
        elif err_str.startswith("Can't locate revision identified by"):
            rev_id = re.findall(" '(.*)'$",err_str)[0].replace("'","'").strip()
            flask_migrate.revision(rev_id=rev_id)
    finally:
        if try_again:
            flask_migrate.migrate()