import pytest
from django.db.models import Model

from ..mixins import ResourceModelMixin
from .factories import ResourceFactory
from core.tests.base_test_case import UserTestCase
from core.tests.util import make_dirs  # noqa


class ResourceModel(ResourceModelMixin, Model):
    class Meta:
        app_label = 'core'


@pytest.mark.usefixtures('make_dirs')
class ResourceModelMixinTest(UserTestCase):
    def test_resources_property(self):
        resource_model_1 = ResourceModel()
        resource_model_1.save()

        ResourceFactory.create_batch(2, content_object=resource_model_1)

        resource_model_2 = ResourceModel()
        resource_model_2.save()
        resource_2 = ResourceFactory.create(content_object=resource_model_2)

        assert resource_model_1.resources.count() == 2
        assert resource_2 not in resource_model_1.resources

    def test_reload_resources(self):
        resource_model_1 = ResourceModel()
        resource_model_1.save()
        ResourceFactory.create_batch(2, content_object=resource_model_1)
        assert resource_model_1.resources.count() == 2
        resource_model_1.reload_resources()
        assert not hasattr(resource_model_1, '_resources')
