from . import utils
from . import auth
from . import encode
from . import random
from . import convert
from . import flask
from . import github_issue

from . import importer

from . import system
from . import network


from flask import g, has_app_context


def current_child_id() -> int:
    if has_app_context() and hasattr(g, "child"):
        return g.child.id
    return 0
