"""Factories for BackgroundTask model creation."""
import uuid

import factory

from accounts.tests.factories import UserFactory
from core.tests.factories import ExtendedFactory
from ..models import BackgroundTask
from ..utils.fields import input_field_default


class BackgroundTaskFactory(ExtendedFactory):

    class Meta:
        model = BackgroundTask

    id = str(uuid.uuid1())
    type = 'foo.bar'
    input = factory.LazyFunction(input_field_default)
    creator = factory.SubFactory(UserFactory)
