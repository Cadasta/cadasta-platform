import pytest
from django.test import TestCase
from django.forms import BooleanField
from core.tests.utils.files import make_dirs  # noqa
from ..fields import ResourceField
from ..widgets import ResourceWidget
from .factories import ResourceFactory


@pytest.mark.usefixtures('make_dirs')
class ResourceFieldTest(TestCase):
    def test_init_without_widget(self):
        resource = ResourceFactory.build()
        field = ResourceField(resource=resource)

        assert isinstance(field.widget, ResourceWidget)
        assert field.resource == resource

    def test_init_with_widget(self):
        resource = ResourceFactory.build()
        field = ResourceField(resource=resource, widget=BooleanField())

        assert isinstance(field.widget, BooleanField)
        assert field.resource == resource
