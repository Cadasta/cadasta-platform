import uuid

import factory

from accounts.tests.factories import UserFactory
from core.tests.factories import ExtendedFactory
from ..models import BackgroundTask, TaskResult
from ..utils.fields import input_field_default


def gen_id(length=24):
    return str(uuid.uuid4())[:length]


class BackgroundTaskFactory(ExtendedFactory):

    class Meta:
        model = BackgroundTask

    id = factory.LazyFunction(gen_id)
    task_id = factory.LazyFunction(gen_id)
    root_id = factory.LazyAttribute(lambda o: o.task_id)
    type = 'foo.bar'
    input = factory.LazyFunction(input_field_default)
    creator = factory.SubFactory(UserFactory)


class TaskResultFactory(ExtendedFactory):

    class Meta:
        model = TaskResult

    task = factory.SubFactory(BackgroundTaskFactory)
    result = 'complete'
    status = 'PENDING'
