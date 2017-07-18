import uuid

import factory

from accounts.tests.factories import UserFactory
from core.tests.factories import ExtendedFactory
from ..models import BackgroundTask, TaskResult
from ..utils.fields import input_field_default


class BackgroundTaskFactory(ExtendedFactory):

    class Meta:
        model = BackgroundTask

    id = str(uuid.uuid1())
    type = 'foo.bar'
    input = factory.LazyFunction(input_field_default)
    creator = factory.SubFactory(UserFactory)


class TaskResultFactory(ExtendedFactory):

    class Meta:
        model = TaskResult

    id = str(uuid.uuid1())
    task_id = str(uuid.uuid1())
    result = 'complete'
    status = 'PENDING'
