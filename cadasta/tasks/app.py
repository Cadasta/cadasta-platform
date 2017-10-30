from django.apps import AppConfig


class TasksConfig(AppConfig):
    name = 'tasks'

    def ready(self):
        from .celery import app
        app.autodiscover_tasks(force=True)
