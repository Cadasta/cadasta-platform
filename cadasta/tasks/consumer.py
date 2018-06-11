import logging

import boto3
from django.db import close_old_connections, OperationalError, InterfaceError
from kombu.mixins import ConsumerMixin

from tasks.celery import conf
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
            self._handle_task(body, message)
        except (OperationalError, InterfaceError):
            # Lost DB connection, close DB and don't ack() msg.
            # A new DB connection will be re-opened next time we
            # try to access the DB. Msg will be re-processed
            # after SQS visibility timeout passes.
            logger.exception("DB connection lost. Cleaning up connections")
            return close_old_connections()
        except:  # NOQA
            logger.exception("Failed to process message: %r", message)

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
        region = conf.broker_transport_options.get('region', 'us-west-2')
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
        task_type = message.headers['task']

        # Add additional option data from headers to properties
        option_keys = ['eta', 'expires', 'retries', 'timelimit']
        message.properties.update(
            **{k: v for k, v in message.headers.items()
               if k in option_keys and v not in (None, [None, None])})

        props = message.properties
        _, created = BackgroundTask.objects.get_or_create(
            task_id=task_id,
            defaults={
                'type': task_type,
                'input_args': args,
                'input_kwargs': kwargs,
                'options': props,
                'parent_id': message.headers['parent_id'],
                'root_id': message.headers['root_id'],
                'creator_id': props.get('creator_id'),
                'related_content_type_id':
                    props.get('related_content_type_id'),
                'related_object_id': props.get('related_object_id'),
            }
        )
        if created:
            logger.debug("Processed task: %r", message)
        else:
            logger.warn("Task already existed in db: %r", message)
