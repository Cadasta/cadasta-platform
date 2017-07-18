from __future__ import absolute_import

from celery import Celery
from cadasta.workertoolbox.conf import Config


app = Celery('app')
app.config_from_object(
    Config(queues=('export',))
)
