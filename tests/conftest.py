import sys
import pytest

from hiddifypanel import create_app
from hiddifypanel.panel.commands import init_db
from hiddifypanel.panel.database import db


@pytest.fixture(scope="session")
def app():
    app = create_app(FORCE_ENV_FOR_DYNACONF="testing")
    with app.app_context():
        db.create_all(app=app)
        yield app
        db.drop_all(app=app)


@pytest.fixture(scope="session")
def products(app):
    with app.app_context():
        return init_db()


# each test runs on cwd to its temp dir
@pytest.fixture(autouse=True)
def go_to_tmpdir(request):
    # Get the fixture dynamically by its name.
    tmpdir = request.getfixturevalue("tmpdir")
    # ensure local test created packages can be imported
    sys.path.insert(0, str(tmpdir))
    # Chdir only for the duration of the test.
    with tmpdir.as_cwd():
        yield
