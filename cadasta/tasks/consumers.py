import logging

from celery import bootsteps
from celery.app.trace import build_tracer
from celery.backends.base import DisabledBackend
from celery.exceptions import InvalidTaskError
from celery.worker.consumer import Consumer
from django.conf import settings
from django.db.models import F
from django.db.models.expressions import CombinedExpression, Value
from kombu import Queue, Consumer as KombuConsumer
from vine import promise

from .celery import app


logger = logging.getLogger(__name__)


# @app.task(name='result_consumer.process_task')
def process_task(message):
    from .models import BackgroundTask
    """ Add scheduled tasks to database """
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
        raise InvalidTaskError("Failed to parse task.")


# @app.task(name='result_consumer.process_result')
def process_result(message):
    """ Handle result message """
    try:
        result = message.payload
        logger.debug('Received message: {0!r}'.format(result))
        task_qs = BackgroundTask.objects.filter(id=result['task_id'])
        # from celery.contrib import rdb; rdb.set_trace()
        assert task_qs.exists()

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
        raise InvalidTaskError("Failed to process task result.")


# class ResultConsumerStep(bootsteps.StartStopStep):
# # class ResultConsumerStep(bootsteps.ConsumerStep):
#     requires = ('celery.worker.consumer:Tasks', )
#     def start(self, parent):
#         valid_queues = [
#             settings.CELERY_DEFAULT_QUEUE,
#             settings.CELERY_RESULT_QUEUE
#         ]
#         # from celery.contrib import rdb
#         # rdb.set_trace()
#         for name, q in parent.app.amqp.queues.items():
#             if name not in valid_queues:
#                 parent.cancel_task_queue(name)

#         to_rm = []
#         for task in parent.task_buckets:
#             if not task.startswith('result_consumer'):
#                 to_rm.append(task)
#         for task in to_rm:
#             parent.task_buckets.pop(task)

#         # parent.cancel_task_queue(app.conf.CELERY_DEFAULT_QUEUE)
#         # parent.add_task_queue('{}.{}'.format(some_id, self.my_queue))


# class ResultConsumerStep(bootsteps.ConsumerStep):
#     """
#     Reads off the Result queue, inserting messages into DB.

#     NOTE: This only works if you run a celery worker that is NOT looking
#     at the Result queue. Ex. "celery -A config worker"
#     """

#     # def __init__(self, *args, **kwargs):
#     #     if settings.CELERY_RESULT_QUEUE in app.app_or_default().amqp.queues:
#     #         msg = (
#     #             "Error: Please don't specify the result queue (\"{}\") as a "
#     #             "queue to be consumed by the worker. Result messages aren't "
#     #             "encoded in the same format as Task messages. Bad things will "
#     #             "happen."
#     #         )
#     #         raise ValueError(msg.format(settings.CELERY_RESULT_QUEUE))
#     #     super(ResultConsumer, self).__init__(*args, **kwargs)

#     @staticmethod
#     def _detect_msg_type(message):
#         if 'task' in message.headers:
#             return 'task'
#         if 'result' in message.payload:
#             return 'result'
#         raise TypeError("Cannot detect message type")

#     def get_consumers(self, channel):
#         return [KombuConsumer(channel,
#                          queues=[Queue('result_queue.fifo')],
#                          callbacks=[self.handle_message],
#                          accept=['json'])]

#     def handle_message(self, body, message):
#         # from celery.contrib import rdb
#         # rdb.set_trace()

#         try:
#             handler = {
#                 'task': process_task,
#                 'result': process_result
#             }[self._detect_msg_type(message)]
#             handler(message)

#             # logger.debug('Received message: {0!r}'.format(body))
#             # task_qs = BackgroundTask.objects.filter(id=body['task_id'])
#             # assert task_qs.exists()

#             # status = body.get('status')
#             # if status:
#             #     task_qs.update(status=status)

#             # result = body['result']
#             # if status in BackgroundTask.DONE_STATES:
#             #     task_qs.update(output=result)
#             # else:
#             #     assert isinstance(result, dict), (
#             #         "Malformed result data, expecting a dict"
#             #     )
#             #     log = result.get('log')
#             #     if log:
#             #         task_qs.update(log=CombinedExpression(
#             #             F('log'), '||', Value([log])
#             #         ))
#         except:
#             logger.exception("Failed to process task")
#         finally:
#             try:
#                 message.ack()
#             except:
#                 logger.exception("Failed to acknowledge message")

class WorkerStep(bootsteps.Step):
    def start(self, worker):
        from celery.contrib import rdb
        rdb.set_trace()
        for task in [t for t in self.app.tasks]:
            if not task.startswith('result_consumer'):
                self.app.tasks.unregister(task)
                print("Rm {!r}".format(task))


class ResultConsumer(Consumer):
    def __init__(self, *args, **kwargs):
        super(ResultConsumer, self).__init__(*args, **kwargs)
        # from celery.contrib import rdb
        # rdb.set_trace()
        # print(type(self.app.tasks))
        for task in [t for t in self.app.tasks]:
            if not task.startswith('result_consumer'):
                self.app.tasks.unregister(task)
        # self.app.tasks = {
        #     k: v for k, v in self.app.tasks.items()
        #     if k.startswith('result_consumer')}

        # valid_queues = [
        #     settings.CELERY_DEFAULT_QUEUE,
        #     settings.CELERY_RESULT_QUEUE
        # ]
        # # from celery.contrib import rdb
        # # rdb.set_trace()
        # for name, q in self.app.amqp.queues.items():
        #     if name not in valid_queues:
        #         self.cancel_task_queue(name)
        # from celery.contrib import rdb
        # rdb.set_trace()
        # # self.app.backend = DisabledBackend(self.app)

    def update_strategies(self):
        self.strategies = {
            'task': process_task,
            'result': process_result,
        }
        loader = self.app.loader
        for name, task in self.strategies.items():
            self.strategies[name] = task.start_strategy(self.app, self)
            task.__trace__ = build_tracer(name, task, loader, self.hostname,
                                          app=self.app)

    @staticmethod
    def _detect_msg_type(message):
        if 'task' in message.headers:
            return 'task'
        if 'result' in message.payload:
            return 'result'
        raise TypeError("Cannot detect message type")

    def create_task_handler(self, promise=promise):
        strategies = self.strategies
        on_unknown_message = self.on_unknown_message
        on_unknown_task = self.on_unknown_task
        on_invalid_task = self.on_invalid_task
        callbacks = self.on_task_message
        call_soon = self.call_soon

        def on_task_received(message):
            # from celery.contrib import rdb; rdb.set_trace()

            try:
                type_ = self._detect_msg_type(message)
            except TypeError as exc:
                return on_unknown_message(None, message, exc)
            try:
                strategy = strategies[type_]
            except KeyError as exc:
                return on_unknown_task(None, message, exc)
            try:
                strategy(
                    message, None,
                    promise(call_soon, (message.ack_log_error,)),
                    promise(call_soon, (message.reject_log_error,)),
                    callbacks,
                )
            except InvalidTaskError as exc:
                return on_invalid_task(None, message, exc)

        return on_task_received
