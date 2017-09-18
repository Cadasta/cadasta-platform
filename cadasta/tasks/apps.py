from django.apps import AppConfig
from cadasta.workertoolbox.setup import setup_app


class TasksConfig(AppConfig):
    name = 'tasks'

    def ready(self):
        from .celery import app
        app.autodiscover_tasks(force=True)
        setup_app(app, throw=True)
