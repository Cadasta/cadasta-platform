from celery import Task
from django.test import TestCase

from .. import tasks


class TestTasks(TestCase):
    def test_hello(self):
        assert isinstance(tasks.hello, Task)
        assert tasks.hello.name == 'export.hello'
        tasks.hello(name='Cadasta!')

    def test_email_msg(self):
        assert isinstance(tasks.email_msg, Task)
        assert tasks.email_msg.name == 'export.email_msg'
        tasks.email_msg(msg='my_msg', to_address='to_address')
