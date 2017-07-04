import os

import factory
from accounts.tests.factories import UserFactory
from buckets.test.storage import FakeS3Storage
from core.tests.factories import ExtendedFactory
from django.conf import settings
from django.utils import timezone
from organization.tests.factories import ProjectFactory

from ..models import Resource, SpatialResource

path = os.path.dirname(settings.BASE_DIR)


class ResourceFactory(ExtendedFactory):

    class Meta:
        model = Resource

    name = factory.Sequence(lambda n: "Resouce #%s" % n)
    description = factory.Sequence(lambda n: "Resource #%s description" % n)
    original_file = 'image.jpg'
    contributor = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)

    @classmethod
    def _prepare(cls, create, **kwargs):
        resource = super()._prepare(create, **kwargs)

        if not resource.file.url:
            storage = FakeS3Storage()
            file = open(path + '/resources/tests/files/image.jpg', 'rb')
            file_name = storage.save('resources/image.jpg', file.read())
            file.close()

            resource.file = file_name
            if create:
                resource.save()

        return resource


class SpatialResourceFactory(ExtendedFactory):

    class Meta:
        model = SpatialResource

    name = factory.Sequence(lambda n: "LayerName #%s" % n)
    time = timezone.now()
    resource = factory.SubFactory(ResourceFactory)
