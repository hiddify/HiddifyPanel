from apiflask import APIFlask, Schema, abort
from apiflask.fields import Integer, String, UUID, Boolean, Enum, Float, Date, Time
from apiflask.validators import Length, OneOf

from hiddifypanel.models import *


class Success(Schema):
    pass
