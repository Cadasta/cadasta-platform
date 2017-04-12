from __future__ import absolute_import

from celery import Celery
from .signals import *  # NOQA


app = Celery('app')
app.config_from_object('app.celeryconfig')
