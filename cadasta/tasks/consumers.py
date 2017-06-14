import logging

from celery.app.trace import build_tracer
from celery.exceptions import InvalidTaskError
from celery.worker.consumer import Consumer
from django.db.models import F
from django.db.models.expressions import CombinedExpression, Value
from vine import promise

from .celery import app
from .models import BackgroundTask


logger = logging.getLogger(__name__)


@app.task()
def process_task(message):
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


@app.task()
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


class ResultConsumer(Consumer):
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
