#!/opt/hiddify-manager/.venv/bin/python

from hiddifypanel import create_app_wsgi
from asgiref.wsgi import WsgiToAsgi

app = create_app_wsgi()  # noqa
asgi_app = WsgiToAsgi(app)
