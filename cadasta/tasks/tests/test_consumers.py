from unittest.mock import patch, MagicMock, call

from django.test import TestCase, override_settings
from django.db.models import F
from django.db.models.expressions import CombinedExpression, Value

from tasks.consumers import MessageConsumer
from tasks.tests.factories import BackgroundTaskFactory


@override_settings(CELERY_RESULT_QUEUE='results-queue')
class TestConsumers(TestCase):

    @patch('celery.app.app_or_default')
    @patch('tasks.consumers.bootsteps.ConsumerStep.__init__')
    def test_validate_queues(self, consumer_init, get_mock_app):
        """
        Ensure that consumer throws exception if worker processing Results
        queue.
        """
        mock_app = MagicMock()
        get_mock_app.return_value = mock_app
        mock_app.amqp.queues = ['foo', 'results-queue']

        with self.assertRaises(ValueError):
            MessageConsumer()
        self.assertFalse(consumer_init.called)

        # Correct setup
        mock_app.amqp.queues = ['foo', 'bar']
        MessageConsumer()
        consumer_init.assert_called_once_with()

    @patch('tasks.consumers.bootsteps.ConsumerStep.__init__', MagicMock())
    def test_get_queues(self):
        consumers = MessageConsumer().get_consumers(MagicMock())
        self.assertEqual(len(consumers), 1)
        consumer = consumers[0]
        self.assertEqual(len(consumer.queues), 1)
        queue = consumer.queues[0]
        queue.name == 'results-queue'

    @patch('tasks.consumers.bootsteps.ConsumerStep.__init__', MagicMock())
    @patch('tasks.consumers.BackgroundTask.objects.filter')
    def test_message_handler_completed(self, mock_filter):
        """
        Ensure completed tasks set output to the output property.
        """
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs

        fake_body = {
            'task_id': '123',
            'status': 'SUCCESS',
            'result': 'All succeeded',
        }
        mock_msg = MagicMock()
        MessageConsumer().handle_message(fake_body, mock_msg)
        mock_qs.update.assert_has_calls([
            call(status='SUCCESS'),
            call(output='All succeeded')
        ])
        mock_msg.ack.assert_called_once_with()

    @patch('tasks.consumers.bootsteps.ConsumerStep.__init__', MagicMock())
    @patch('tasks.consumers.BackgroundTask.objects.filter')
    def test_message_handler_in_progress_dict_log(self, mock_filter):
        """
        Ensure in-progess tasks append output dict with log key to the log.
        """
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs

        fake_body = {
            'task_id': '123',
            'status': 'PROGRESS',
            'result': {'log': 'Things are coming along'},
        }
        mock_msg = MagicMock()
        MessageConsumer().handle_message(fake_body, mock_msg)
        calls = mock_qs.update.call_args_list
        self.assertEqual(calls[0], call(status='PROGRESS'))
        self.assertEqual(
            str(calls[1]),
            str(call(log=CombinedExpression(
                F('log'), '||', Value(['Things are coming along'])
            )))
        )
        mock_msg.ack.assert_called_once_with()

    @patch('tasks.consumers.bootsteps.ConsumerStep.__init__', MagicMock())
    @patch('tasks.consumers.logger')
    def test_message_handler_handles_exceptions(self, mock_log):
        """
        Ensure that exceptions in task parsing are handled gracefully
        """
        mock_msg = MagicMock()
        empty_body = {}
        MessageConsumer().handle_message(empty_body, mock_msg)
        mock_msg.ack.assert_called_once_with()
        self.assertEqual(mock_log.exception.call_count, 1)

    @patch('tasks.consumers.bootsteps.ConsumerStep.__init__', MagicMock())
    @patch('tasks.consumers.BackgroundTask.objects.filter')
    @patch('tasks.consumers.logger')
    def test_message_handler_handles_failed_ack(self, mock_log, mock_filter):
        """
        Ensure that exceptions in task parsing are handled gracefully
        """
        task = BackgroundTaskFactory.build(status='PENDING')
        mock_filter.exists.return_value = True
        task.save = MagicMock()
        fake_body = {
            'task_id': '123',
            'status': 'PROGRESS',
            'result': {'log': 'Things are coming along'},
        }
        ack_func = MagicMock(side_effect=Exception("Failed ack"))
        mock_msg = MagicMock(ack=ack_func)
        MessageConsumer().handle_message(fake_body, mock_msg)
        ack_func.assert_called_once_with()
        self.assertEqual(mock_log.exception.call_count, 1)
