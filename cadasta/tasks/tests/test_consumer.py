from collections import namedtuple
from unittest.mock import patch, MagicMock, call

from django.test import TestCase, override_settings

from tasks.consumer import Worker


@override_settings(CELERY_BROKER_TRANSPORT_OPTIONS={'region': 'us-west-2'})
class TestConsumers(TestCase):

    def setUp(self):
        self.mock_conn = MagicMock(as_uri=MagicMock(return_value='sqs://'))
        self.mock_queues = MagicMock()
        self.mock_worker = Worker(
            connection=self.mock_conn, queues=self.mock_queues)

    def get_task_msg(self, chain=None):
        args, kwargs = [], {}
        headers = {
            'kwargsrepr': '{}',
            'retries': 0,
            'eta': None,
            'timelimit': [None, None],
            'task': 'export.hello',
            'expires': None,
            'origin': 'gen4340@vagrant-ubuntu-trusty-64',
            'parent_id': None,
            'group': None,
            'lang': 'py',
            'root_id': '486e8738-a9ef-475a-b8e1-158e987f4ae6',
            'argsrepr': '()',
            'id': '486e8738-a9ef-475a-b8e1-158e987f4ae6'
        }
        return MagicMock(
            headers=headers,
            payload=[
                args, kwargs,
                {'callbacks': None, 'chain': chain,
                 'errbacks': None, 'chord': None}
            ],
            decode=MagicMock(return_value=(args, kwargs, headers)),
            properties={}
        )

    @staticmethod
    def assert_sqs_ack(sqs_client, msg):
        return sqs_client.delete_message.assert_called_once_with(
            QueueUrl=msg.delivery_info['sqs_queue'],
            ReceiptHandle=msg.delivery_info['sqs_message']['ReceiptHandle']
        )

    def test_get_queues(self):
        MockConsumer = namedtuple('Consumer', 'queues,accept,callbacks')
        MockQueue = namedtuple('Queue', 'name')
        mock_channel = MagicMock()
        w = Worker(
            connection=self.mock_conn,
            queues=[MockQueue(name='foobar')]
        )
        consumers = w.get_consumers(MockConsumer, mock_channel)

        assert len(consumers) == 1
        consumer = consumers[0]
        assert len(consumer.queues) == 1
        queue = consumer.queues[0]
        assert queue.name == 'foobar'

        assert len(consumer.callbacks) == 1
        assert consumer.callbacks[0] == w.process_task

    @patch('tasks.consumer.logger')
    @patch('tasks.consumer.Worker._handle_task')
    @patch('tasks.consumer.boto3.client')
    def test_process_task_handles_failed_parsing(
            self, boto3_client, handle_task, logger):
        """
        Ensure that process_task() gracefully handles message parsing failures
        """
        body = MagicMock()
        msg = MagicMock()
        sqs_client = MagicMock()
        boto3_client.return_value = sqs_client
        handle_task.side_effect = Exception()

        self.mock_worker.process_task(body, msg)

        assert logger.exception.call_count == 1
        self.assert_sqs_ack(sqs_client, msg)
        logger.exception.assert_called_once_with(
            'Failed to process message: %r', msg)

    @patch('tasks.consumer.logger')
    @patch('tasks.consumer.Worker._handle_task', MagicMock())
    def test_non_sqs_ack(self, logger):
        """
        Ensure that non-sqs connections correctly ack messages
        """
        msg = MagicMock()
        body = MagicMock()
        self.mock_worker.connection.as_uri = MagicMock(return_value='amqp://')

        self.mock_worker.process_task(body, msg)

        msg.ack.assert_called_once_with()
        assert logger.exception.call_count == 0

    @patch('tasks.consumer.logger')
    @patch('tasks.consumer.BackgroundTask')
    def test_handle_new_task(self, BackgroundTask, logger):
        body = MagicMock()
        msg = self.get_task_msg()
        BackgroundTask.objects.get_or_create.return_value = (None, True)

        self.mock_worker._handle_task(body, msg)

        BackgroundTask.objects.get_or_create.assert_called_once_with(
            defaults={
                'type': 'export.hello',
                'root_id': '486e8738-a9ef-475a-b8e1-158e987f4ae6',
                'input_kwargs': {},
                'input_args': [],
                'options': {'retries': 0},
                'parent_id': None
            },
            task_id='486e8738-a9ef-475a-b8e1-158e987f4ae6'
        )
        assert logger.debug.call_args_list == [
            call('Handling task message %r', body),
            call('Processed task: %r', msg)]

    @patch('tasks.consumer.logger')
    @patch('tasks.consumer.BackgroundTask')
    def test_handle_existing_task(self, BackgroundTask, logger):
        """
        Ensure handle_task logs already existing task as warning.
        """
        body = MagicMock()
        msg = self.get_task_msg()
        BackgroundTask.objects.get_or_create.return_value = (None, False)

        self.mock_worker._handle_task(body, msg)

        BackgroundTask.objects.get_or_create.assert_called_once_with(
            defaults={
                'type': 'export.hello',
                'root_id': '486e8738-a9ef-475a-b8e1-158e987f4ae6',
                'input_kwargs': {},
                'input_args': [],
                'options': {'retries': 0},
                'parent_id': None
            },
            task_id='486e8738-a9ef-475a-b8e1-158e987f4ae6'
        )
        logger.debug.assert_called_once_with(
            'Handling task message %r', body)
        logger.warn.assert_called_once_with(
            "Task already existed in db: %r", msg)
