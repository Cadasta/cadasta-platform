import logging
import time

from celery import bootsteps
from django.conf import settings
from django.db.models import F
from django.db.models.expressions import CombinedExpression, Value
from kombu import Consumer, Queue

from .models import BackgroundTask


logger = logging.getLogger(__name__)


from celery import bootsteps


class ExampleWorkerStep(bootsteps.StartStopStep):
    # def __init__(self, worker, **kwargs):
    #     print('Called when the WorkController instance is constructed')
    #     print('Arguments to WorkController: {0!r}'.format(kwargs))

    def create(self, worker):
        # this method can be used to delegate the action methods
        # to another object that implements ``start`` and ``stop``.
        logger.warn('Disabling queues')
        worker.app.amqp.queues = {}
        return self

    def start(self, worker):
        print('Called when the worker is started.')

    def stop(self, worker):
        print('Called when the worker shuts down.')

    def terminate(self, worker):
        print('Called when the worker terminates')


class ResultConsumerStep(bootsteps.ConsumerStep):
    """
    Reads off the Result queue, inserting messages into DB.
    NOTE: This only works if you run a celery worker that is NOT looking
    at the Result queue. Ex. "celery -A config worker"
    """

    # def __init__(self, *args, **kwargs):
    #     print(app.app_or_default().amqp.queues)
    #     super(ResultConsumerStep, self).__init__(*args, **kwargs)

    def get_consumers(self, channel):
        return [
            Consumer(
                channel,
                queues=[Queue(settings.TASK_DUPLICATE_QUEUE)],
                callbacks=[self.handle_task],
                accept=['json']),
            Consumer(
                channel,
                queues=[Queue(settings.CELERY_RESULT_QUEUE)],
                callbacks=[self.handle_result],
                accept=['json']),
        ]

    def handle_task(self, body, message):
        logger.debug("Handling task message %r", body)
        try:
            args, kwargs, options = message.decode()
            task_id = message.headers['id']

            # Add default properties
            option_keys = ['eta', 'expires', 'retries', 'timelimit']
            message.properties.update(
                **{k: v for k, v in message.headers.items()
                   if k in option_keys and v not in (None, [None, None])})

            # Ensure chained followup tasks contain proper data
            chain_parent_id = task_id[:]
            chain = options.get('chain') or []
            for t in chain[::-1]:  # Chain array comes in reverse order
                t['parent_id'] = chain_parent_id
                chain_parent_id = t['options']['task_id']

            # TODO: Add support for grouped tasks
            # TODO: Add support tasks gednerated by workers
            _, created = BackgroundTask.objects.get_or_create(
                id=task_id,
                defaults={
                    'type': message.headers['task'],
                    'input_args': args,
                    'input_kwargs': kwargs,
                    'options': message.properties,
                    'parent_id': message.headers['parent_id'],
                    'root_id': message.headers['root_id'],
                }
            )
            if created:
                logger.debug("Processed task: %r", message)
            else:
                logger.warn("Task already existed in db: %r", message)
        except:
            logger.exception("Failed to parse task.")
        finally:
            message.ack()

    def handle_result(self, body, message):
        """ Handle result message """
        logger.debug("Handling result message %r", body)
        try:
            result = message.payload
            logger.debug('Received message: {0!r}'.format(result))
            task_id = result['task_id']
            task_qs = BackgroundTask.objects.filter(id=task_id)

            attempts = 0
            while not task_qs.exists():
                logger.debug("No corresponding task found (%r), retrying...", task_id)
                if attempts > 3:
                    logger.exception("No corresponding task found, exiting...\n%r", result)
                    return
                time.sleep(1)
                attempts += 1

            status = result.get('status')
            if status:
                task_qs.update(status=status)

            result = result['result']
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
            logger.exception("Failed to process task result.")
        finally:
            message.ack()
