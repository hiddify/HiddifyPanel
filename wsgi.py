#!/opt/hiddify-manager/.venv/bin/python

from hiddifypanel import create_app_wsgi

app = application = create_app_wsgi()  # noqa
from asgiref.wsgi import WsgiToAsgi
asgi_app = WsgiToAsgi(app)
celery_app=app.extensions["celery"]
if __name__ == "__main__":
    app.run()
