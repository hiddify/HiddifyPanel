from flask_admin.base import AdminIndexView,expose
from hiddifypanel.panel.hiddify  import admin
from flask import render_template

from flask_classful import FlaskView

class Dashboard(FlaskView):
    def index(self):
        return render_template('index.html')