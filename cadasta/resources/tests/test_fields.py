from django.test import TestCase
from django.forms import BooleanField
from ..fields import ResourceField
from ..widgets import ResourceWidget
from .factories import ResourceFactory


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
