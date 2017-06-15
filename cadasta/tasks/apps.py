from django.apps import AppConfig
from django.conf import settings
from kombu import Queue


class TasksConfig(AppConfig):
    name = 'tasks'

    def ready(self):
        # from . import signals  # NOQA
        from .celery import app
        # from .consumers import ResultConsumerStep, WorkerStep
        # app.steps['worker'].add(WorkerStep)
        app.autodiscover_tasks(force=True)

        # Setup exchanges
        with app.producer_or_acquire() as P:
            # Ensure all queues are registered with proper exchanges
            for q in app.amqp.queues.values():
                P.maybe_declare(q)

            # Ensure Result queue is set up
            P.maybe_declare(Queue(
                settings.CELERY_RESULT_QUEUE,
                app.backend.exchange,
                routing_key='#'))
