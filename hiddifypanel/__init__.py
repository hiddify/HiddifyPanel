
from .VERSION import __version__, __release_date__
from . import Events
from .base import create_app, create_app_wsgi
from . import panel


# from .model import Child
# current_child:LocalProxy(lambda:g.get("__child",Child.query.filter(Child.id==current_child_id).first())

__all__ = ["create_app", "create_app_wsgi"]

# application = create_app_wsgi()
