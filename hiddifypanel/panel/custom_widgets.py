import datetime

from flask_admin.contrib.sqla import ModelView
from flask_babel import lazy_gettext as _
from wtforms import TextAreaField
from wtforms.fields import IntegerField, SelectField, DecimalField
from wtforms.widgets import TextArea

from hiddifypanel.models import *


# from gettext import gettext as _


class DaysLeftField(IntegerField):
    def process_data(self, value):
        if value is not None:
            days_left = (value - datetime.date.today()).days
            self.data = days_left
        else:
            self.data = None

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            days_left = valuelist[0]
            new_date_value = datetime.date.today() + datetime.timedelta(days=int(days_left))
            self.data = new_date_value
        else:
            self.data = None


class LastResetField(IntegerField):
    def process_data(self, value):
        if value is not None:
            days_left = (datetime.date.today() - value).days
            self.data = days_left
        else:
            self.data = None

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            days_left = valuelist[0]
            new_date_value = datetime.date.today() - datetime.timedelta(days=int(days_left))
            self.data = new_date_value
        else:
            self.data = None


class CKTextAreaWidget(TextArea):
    extra_js = ['//cdn.ckeditor.com/4.6.0/standard/ckeditor.js']

    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] += ' ckeditor'
        else:
            kwargs.setdefault('class', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(TextAreaField):
    extra_js = ['//cdn.ckeditor.com/4.6.0/standard/ckeditor.js']
    widget = CKTextAreaWidget()


class MessageAdmin(ModelView):
    extra_js = ['//cdn.ckeditor.com/4.6.0/standard/ckeditor.js']

    form_overrides = {
        'body': CKTextAreaField
    }


class EnumSelectField(SelectField):
    def __init__(self, enum, *args, **kwargs):
        choices = [(str(enum_value.value), _(enum_value.name)) for enum_value in enum]
        super().__init__(*args, choices=choices, **kwargs)


class UsageField(DecimalField):
    def process_data(self, value):
        if value is not None:
            self.data = value / ONE_GIG
        else:
            self.data = None

    def process_formdata(self, valuelist):

        if valuelist and valuelist[0]:
            self.data = int(float(valuelist[0]) * ONE_GIG)
        else:
            self.data = None
