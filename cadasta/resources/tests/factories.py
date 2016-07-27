import os
import factory
from django.conf import settings
from core.tests.factories import ExtendedFactory
from organization.tests.factories import ProjectFactory
from accounts.tests.factories import UserFactory

from ..models import Resource

from buckets.test.storage import FakeS3Storage
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
            file = open(path + '/resources/tests/files/image.jpg', 'rb').read()
            file_name = storage.save('resources/image.jpg', file)

            resource.file = file_name
            if create:
                resource.save()

        return resource
