import logging

import boto3
from django.conf import settings
from kombu.mixins import ConsumerMixin

from .models import BackgroundTask


logger = logging.getLogger(__name__)


class Worker(ConsumerMixin):

    def __init__(self, connection, queues):
        self.connection = connection
        self.queues = queues
        super(Worker, self).__init__()
        logger.info("Started worker %r for queues %r", self, self.queues)

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=self.queues,
                         accept=['pickle', 'json'],
                         callbacks=[self.process_task])]

    def process_task(self, body, message):
        logger.info('Processing message: %r', message)
        try:
            return self._handle_task(body, message)
        except:
            logger.exception("Failed to process message: %r", message)
        finally:
            logger.info("ACKing message %r", message)
            if self.connection.as_uri().lower().startswith('sqs://'):
                # HACK: Can't seem to get message.ack() to work for SQS
                # backend. Without this hack, messages will keep
                # re-appearing after the visibility_timeout expires.
                # See https://github.com/celery/kombu/issues/758
                return self._sqs_ack(message)
            return message.ack()

    def _sqs_ack(self, message):
        logger.debug("Manually ACKing SQS message %r", message)
        region = settings.CELERY_BROKER_TRANSPORT_OPTIONS['region']
        boto3.client('sqs', region).delete_message(
            QueueUrl=message.delivery_info['sqs_queue'],
            ReceiptHandle=message.delivery_info['sqs_message']['ReceiptHandle']
        )
        message._state = 'ACK'
        message.channel.qos.ack(message.delivery_tag)

    @staticmethod
    def _handle_task(body, message):
        logger.debug("Handling task message %r", body)
        args, kwargs, options = message.decode()
        task_id = message.headers['id']

        # Add default properties
        option_keys = ['eta', 'expires', 'retries', 'timelimit']
        message.properties.update(
            **{k: v for k, v in message.headers.items()
               if k in option_keys and v not in (None, [None, None])})

        _, created = BackgroundTask.objects.get_or_create(
            task_id=task_id,
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
