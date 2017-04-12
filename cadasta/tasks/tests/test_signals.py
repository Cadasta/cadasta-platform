from unittest.mock import patch

from celery import Signature, chain
from django.test import TestCase, override_settings

from tasks.celery import app
from tasks.models import BackgroundTask
from tasks.signals import create_model


@override_settings(CELERY_TASK_ROUTES={
    'foo.*': {'queue': 'foo_q'},
    'bar.*': {'queue': 'bar_q'}
})
@override_settings(CELERY_TASK_DEFAULT_QUEUE='default-queue')
@override_settings(CELERY_RESULT_QUEUE='result-queue')
class TestSignals(TestCase):

    def setUp(self):
        # Ensure new routes are applied
        app.amqp.flush_routes()
        app.amqp.router = app.amqp.Router()

    @staticmethod
    def get_payload(chain=False):
        """
        An example of the payload kwargs provided to the 'before_task_publish'
        signal.
        """
        return {
            'declare': [app.amqp.router.queues['foo']],
            'properties': {
                'correlation_id': 'first-task-id',
                'reply_to': 'fd5d7aab-5232-3c34-b406-9d56d6fccad5'
            },
            'routing_key': 'foo',
            'exchange': '',
            'body': (('first'), {'foo': 'bar'}, {
                "errbacks": None,
                "callbacks": None,
                "chord": None,
                "chain": [Signature(s) for s in [
                    {
                        "chord_size": None,
                        "task": "foo.email_results",
                        "subtask_type": None,
                        "immutable": False,
                        "kwargs": {},
                        "args": [],
                        "options": {
                            "reply_to": "fd5d7aab-5232-3c34-b406-9d56d6fccad5",
                            "task_id": "third-task-id"
                        }
                    },
                    {
                        "chord_size": None,
                        "task": "bar.asdf",
                        "subtask_type": None,
                        "immutable": True,
                        "kwargs": {},
                        "args": ["second"],
                        "options": {
                            "countdown": 1,
                            "reply_to": "fd5d7aab-5232-3c34-b406-9d56d6fccad5",
                            "task_id": "second-task-id"
                        }
                    }
                ]] if chain else []
            }),
            'sender': 'foo.asdf',
            'signal': None,  # Normally this is a Signal instance.
            'retry_policy': None,
            'headers': {
                'origin': 'gen28501@vagrant-ubuntu-trusty-64',
                'lang': 'py',
                'timelimit': [None, None],
                'retries': 0,
                'kwargsrepr': '{}',
                'expires': None,
                'group': None,
                'task': 'foo.asdf',
                'parent_id': None,
                'root_id': 'first-task-id',
                'eta': '2017-05-24T16:38:20.312477+00:00',
                'id': 'first-task-id',
                'argsrepr': '()'
            }
        }

    def test_create_single_task(self):
        """ Ensure task is created in the DB """
        payload = self.get_payload(chain=False)
        create_model(**payload)
        tasks = BackgroundTask.objects.all()
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(task.id, 'first-task-id')
        self.assertEqual(task.type, 'foo.asdf')
        self.assertEqual(task.immutable, None)
        self.assertEqual(task.input, {
            'args': 'first', 'kwargs': {'foo': 'bar'}})
        self.assertEqual(task.options, {
            'queue': 'foo_q',
            'eta': '2017-05-24T16:38:20.312477+00:00',
            'reply_to': 'result-queue',
            'retries': 0,
            'correlation_id': 'first-task-id'})

    def test_create_chained_task(self):
        """ Ensure chained tasks are created in the DB """
        payload = self.get_payload(chain=True)
        create_model(**payload)
        self.assertEqual(BackgroundTask.objects.count(), 3)
        t1 = BackgroundTask.objects.get(id='first-task-id')
        self.assertEqual(t1.id, 'first-task-id')
        self.assertEqual(t1.type, 'foo.asdf')
        self.assertEqual(t1.immutable, None)
        self.assertEqual(t1.input, {
            'args': 'first', 'kwargs': {'foo': 'bar'}})
        self.assertEqual(t1.options, {
            'queue': 'foo_q',
            'eta': '2017-05-24T16:38:20.312477+00:00',
            'reply_to': 'result-queue',
            'retries': 0,
            'correlation_id': 'first-task-id'})

        self.assertEqual(t1.children.count(), 1)
        t2 = t1.children.first()
        self.assertEqual(t2.id, 'second-task-id')
        self.assertEqual(t2.parent_id, 'first-task-id')
        self.assertEqual(t2.root_id, 'first-task-id')
        self.assertEqual(t2.type, 'bar.asdf')
        self.assertEqual(t2.immutable, True)
        self.assertEqual(t2.input, {'args': ['second'], 'kwargs': {}})
        self.assertEqual(t2.options, {
            'queue': 'bar_q',
            'countdown': 1,
            'reply_to': 'result-queue',
            'task_id': 'second-task-id',
            'parent_id': 'first-task-id'})

        self.assertEqual(t2.children.count(), 1)
        t3 = t2.children.first()
        self.assertEqual(t3.id, 'third-task-id')
        self.assertEqual(t3.parent_id, 'second-task-id')
        self.assertEqual(t3.root_id, 'first-task-id')
        self.assertEqual(t3.type, 'foo.email_results')
        self.assertEqual(t3.immutable, False)
        self.assertEqual(t3.input, {'args': [], 'kwargs': {}})
        self.assertEqual(t3.options, {
            'queue': 'foo_q',
            'reply_to': 'result-queue',
            'task_id': 'third-task-id',
            'parent_id': 'second-task-id'})

    @patch('tasks.celery.app.amqp.Producer.publish')
    def test_functional_test_task_scheduled(self, send_task):
        """ Ensure task is scheduled and models are created """
        @app.task(name='foo.bar')
        def foo(a_string):
            pass

        foo.delay('fooo')
        self.assertEqual(send_task.call_count, 1)
        ((args, kwargs, options),), details = send_task.call_args
        self.assertEqual(
            (args, kwargs, options),
            (('fooo',), {}, {
                'callbacks': None, 'errbacks': None,
                'chain': None, 'chord': None
            })
        )
        self.assertEqual(details['reply_to'], 'result-queue')
        self.assertEqual(details['queue'], 'foo_q')
        self.assertEqual(BackgroundTask.objects.count(), 1)

    @patch('tasks.celery.app.amqp.Producer.publish')
    def test_functional_test_chain_scheduled(self, send_task):
        """ Ensure chained task is scheduled and models are created """
        @app.task(name='foo.bar')
        def foo(a_string):
            pass

        ch = chain(
            foo.s('first').set(countdown=1),
            foo.si('second').set(countdown=1),
            foo.s())
        ch()
        self.assertEqual(send_task.call_count, 1)
        ((args, kwargs, options),), details = send_task.call_args
        self.assertEqual(details['reply_to'], 'result-queue')
        self.assertEqual(details['queue'], 'foo_q')
        self.assertEqual(BackgroundTask.objects.count(), 3)
