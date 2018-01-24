from unittest.mock import patch, MagicMock

from django.test import TestCase

from tasks.celery import get_app, conf


class TestSetup(TestCase):

    @patch('tasks.celery.breakers.celery.call',
           MagicMock(side_effect=AttributeError))
    @patch('tasks.celery.breakers.celery.expected_errors', (AttributeError,))
    @patch('tasks.celery.logger')
    def test_app_setup_throws_expected_error(self, logger):
        """
        Ensure that if breaker throws expected error, it is logged and
        suppressed.
        """
        get_app(conf)
        logger.exception.assert_called_once_with("Failed to setup celery app.")

    @patch('tasks.celery.breakers.celery.call',
           MagicMock(side_effect=KeyError))
    @patch('tasks.celery.breakers.celery.expected_errors', ())
    @patch('tasks.celery.logger')
    def test_app_setup_throws_unexpected_error(self, logger):
        """
        Ensure that if breaker throws an unexpected error, it is not
        suppressed.
        """
        with self.assertRaises(KeyError):
            get_app(conf)
        assert not logger.exception.called


class TestAmqp(TestCase):

    @patch('tasks.celery.breakers.celery', MagicMock())
    def setUp(self):
        self.app = get_app(conf)

    @patch('tasks.amqp.AMQP.send_task_message')
    @patch('tasks.amqp.setup_app')
    def test_app_setup_is_called(self, setup_app, send_task_message):
        """
        Ensure that app runs setup_app on task scheduling if app has not
        already been set up
        """
        self.app.is_set_up = False

        self.app.send_task('foo')
        setup_app.assert_called_once_with(self.app, throw=True)
        assert send_task_message.call_count == 1
        producer, task, message = send_task_message.call_args_list[0][0]
        assert task == 'foo'

    @patch('tasks.amqp.AMQP.send_task_message')
    @patch('tasks.amqp.setup_app')
    def test_app_setup_is_called__no_flag(self, setup_app, send_task_message):
        """
        Ensure that app runs setup_app on task scheduling if app has not
        already been set up and is_set_up flag is not present
        """
        assert not hasattr(self.app, 'is_set_up')

        self.app.send_task('foo')
        setup_app.assert_called_once_with(self.app, throw=True)
        assert send_task_message.call_count == 1
        producer, task, message = send_task_message.call_args_list[0][0]
        assert task == 'foo'

    @patch('tasks.amqp.AMQP.send_task_message')
    @patch('tasks.amqp.setup_app')
    def test_app_setup_is_not_called(self, setup_app, send_task_message):
        """
        Ensure that app runs setup_app on task scheduling if app has not
        already been set up and is_set_up flag is not present
        """
        self.app.is_set_up = True

        self.app.send_task('foo')
        assert not setup_app.called
        assert send_task_message.call_count == 1
        producer, task, message = send_task_message.call_args_list[0][0]
        assert task == 'foo'
