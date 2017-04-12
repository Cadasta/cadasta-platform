import logging

from celery import bootsteps, app
from django.conf import settings
from django.db.models import F
from django.db.models.expressions import CombinedExpression, Value
from kombu import Consumer, Queue

from .models import BackgroundTask


logger = logging.getLogger(__name__)


class ResultConsumer(bootsteps.ConsumerStep):
    """
    Reads off the Result queue, inserting messages into DB.

    NOTE: This only works if you run a celery worker that is NOT looking
    at the Result queue. Ex. "celery -A config worker"
    """

    def __init__(self, *args, **kwargs):
        if settings.CELERY_RESULT_QUEUE in app.app_or_default().amqp.queues:
            msg = (
                "Error: Please don't specify the result queue (\"{}\") as a "
                "queue to be consumed by the worker. Result messages aren't "
                "encoded in the same format as Task messages. Bad things will "
                "happen."
            )
            raise ValueError(msg.format(settings.CELERY_RESULT_QUEUE))
        super(ResultConsumer, self).__init__(*args, **kwargs)

    def get_consumers(self, channel):
        return [Consumer(channel,
                         queues=[Queue(settings.CELERY_RESULT_QUEUE)],
                         callbacks=[self.handle_message],
                         accept=['json'])]

    def handle_message(self, body, message):
        try:
            logger.debug('Received message: {0!r}'.format(body))
            task_qs = BackgroundTask.objects.filter(id=body['task_id'])
            assert task_qs.exists()

            status = body.get('status')
            if status:
                task_qs.update(status=status)

            result = body['result']
            if status in BackgroundTask.DONE_STATES:
                task_qs.update(output=result)
            else:
                assert isinstance(result, dict), (
                    "Malformed result data, expecting a dict"
                )
                log = result.get('log')
                if log:
                    task_qs.update(log=CombinedExpression(
                        F('log'), '||', Value([log])
                    ))
        except:
            logger.exception("Failed to process task")
        finally:
            try:
                message.ack()
            except:
                logger.exception("Failed to acknowledge message")
