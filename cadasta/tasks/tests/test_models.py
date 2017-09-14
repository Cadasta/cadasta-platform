from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.tests.factories import UserFactory
from core.tests.factories import PolicyFactory
from .factories import BackgroundTaskFactory, TaskResultFactory


class TestTaskResultModel(TestCase):

    def test_str(self):
        task = TaskResultFactory.build(task_id='a1b2c3')
        assert str(task) == 'task=a1b2c3 status=PENDING'


class TestBackgroundTaskModel(TestCase):

    def setUp(self):
        PolicyFactory.load_policies()
        self.user = UserFactory.create()

    def test_str(self):
        task = BackgroundTaskFactory.build(id='a1b2c3', type='some.task')
        assert str(task) == 'id=a1b2c3 type=some.task status=PENDING'

    def test_save_invalid_input_args(self):
        """ Ensure that invalid input args will raise validation error """
        with self.assertRaises(ValidationError) as context:
            BackgroundTaskFactory.build(
                type='foo.bar', input={'args': None},
                creator=self.user
            ).save()
        assert context.exception.error_dict.get('input')

        with self.assertRaises(ValidationError) as context:
            BackgroundTaskFactory.build(
                type='foo.bar', input={'args': {}},
                creator=self.user
            ).save()
        assert context.exception.error_dict.get('input')

    def test_save_invalid_input_kwargs(self):
        """ Ensure that invalid input kwargs will raise validation error """
        with self.assertRaises(ValidationError) as context:
            BackgroundTaskFactory.build(
                type='foo.bar', input={'kwargs': None},
                creator=self.user
            ).save()
        assert context.exception.error_dict.get('input')

        with self.assertRaises(ValidationError) as context:
            BackgroundTaskFactory.build(
                type='foo.bar', input={'kwargs': []},
                creator=self.user
            ).save()
        assert context.exception.error_dict.get('input')

    @patch('tasks.celery.app.tasks', {t: t for t in ['foo.bar']})
    def test_save_valid_input(self):
        """ Ensure that input requires both 'args' and 'kwargs' values. """
        # Missing kwargs
        with self.assertRaises(ValidationError) as context:
            BackgroundTaskFactory.build(
                type='foo.bar', input={'args': []},
                creator=self.user
            ).save()
        assert context.exception.error_dict.get('input')

        # Missing args
        with self.assertRaises(ValidationError) as context:
            BackgroundTaskFactory.build(
                type='foo.bar', input={'kwargs': {}},
                creator=self.user
            ).save()
        assert context.exception.error_dict.get('input')

        # All good
        BackgroundTaskFactory.build(
            type='foo.bar', input={'args': [], 'kwargs': {}},
            creator=self.user
        ).save()

    def test_input_args_property(self):
        """ Ensure that input args getter/setter works as expected """
        task = BackgroundTaskFactory.build(input={'args': [], 'kwargs': {}})
        assert task.input_args == []
        args = ['a', 'b', 'c']
        task.input_args = args
        assert task.input_args == args
        assert task.input == {'args': args, 'kwargs': {}}

    def test_input_kwargs_property(self):
        """ Ensure that input kwargs getter/setter works as expected """
        task = BackgroundTaskFactory.build(input={'args': [], 'kwargs': {}})
        assert task.input_kwargs == {}
        kwargs = {'a': 1, 'b': 2, 'c': 3}
        task.input_kwargs = kwargs
        assert task.input_kwargs == kwargs
        assert task.input == {'args': [], 'kwargs': kwargs}

    def test_overall_status_no_result(self):
        task1 = BackgroundTaskFactory.create()
        # No results, then PENDING
        assert task1.overall_status == 'PENDING'

    def test_overall_status_many_results(self):
        task1 = BackgroundTaskFactory.create()
        TaskResultFactory.create(task_id=task1.task_id, status='SUCCESS')
        task2 = BackgroundTaskFactory.create(root_id=task1.task_id)
        # If multiple statuses and none of which are FAILURE, then STARTED
        assert task1.overall_status == task2.overall_status
        assert task1.overall_status == 'STARTED'

        # If multiple statuses and one of which are FAILURE, then FAILURE
        TaskResultFactory.create(task_id=task2.task_id, status='FAILURE')
        assert task1.overall_status == task2.overall_status
        assert task1.overall_status == 'FAILURE'

    def test_overall_results(self):
        task1 = BackgroundTaskFactory.create()
        TaskResultFactory.create(task_id=task1.task_id, status='SUCCESS')
        task2 = BackgroundTaskFactory.create(
            root_id=task1.task_id,
            options={'is_result': True}
        )

        assert list(task1.overall_results) == list(task2.overall_results)
        assert list(task1.overall_results) == [None]

        out = [{"link": "https://google.com", "text": "Google.com"}]
        TaskResultFactory.create(
            task_id=task2.task_id,
            status='SUCCESS',
            result=out
        )
        assert list(task1.overall_results) == list(task2.overall_results)
        assert list(task1.overall_results) == [out]
