#!/usr/bin/env python3
from flask_classful import FlaskView
from flask_babel import gettext as _
from flask import render_template

from hiddifypanel.models import *


class CommercialInfo(FlaskView):

    def index(self):
        return render_template('commercial_info.html')
