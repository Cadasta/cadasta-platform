from __future__ import absolute_import

from celery import Celery
from .celeryutils import Task


app = Celery('app', task_cls=Task)
app.config_from_object('app.celeryconfig')

if __name__ == '__main__':
    app.start()
