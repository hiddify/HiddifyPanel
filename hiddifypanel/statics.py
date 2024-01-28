from flask import g
from werkzeug.local import LocalProxy
# from .panel.auth import current_account
current_child_id: int = LocalProxy(lambda: g.get('__child_id', 0))
