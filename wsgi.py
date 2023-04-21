#!/usr/bin/env python3

from hiddifypanel import create_app_wsgi

app = application = create_app_wsgi()  # noqa
if __name__ == "__main__":
    app.run()