from collections import namedtuple

from celery import signals
from django.apps import AppConfig


class TasksConfig(AppConfig):
    name = 'tasks'

    def ready(self):
        from .celery import app
        app.autodiscover_tasks(force=True)
        worker = namedtuple('FakeWorker', 'app')
        signals.worker_init.send(sender=worker(app))
