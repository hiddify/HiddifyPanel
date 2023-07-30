#!/usr/bin/env python3
import pprint
from flask_babelex import gettext as _
import pathlib
from hiddifypanel.models import *

from datetime import datetime, timedelta, date
import os
import sys
import json
import urllib.request
import subprocess
import re
from hiddifypanel.panel import hiddify, usage
from flask import current_app, render_template, request, Response, Markup, url_for
from hiddifypanel.panel.hiddify import flash

from flask_classful import FlaskView, route


class CommercialInfo(FlaskView):

    def index(self):
        return render_template('commercial_info.html')
