import os
import factory
from django.conf import settings
from core.tests.factories import ExtendedFactory
from organization.tests.factories import ProjectFactory
from accounts.tests.factories import UserFactory

from ..models import Resource

from buckets.test.utils import ensure_dirs
from buckets.test.storage import FakeS3Storage
path = os.path.dirname(settings.BASE_DIR)

ensure_dirs()
storage = FakeS3Storage()
file = open(path + '/resources/tests/files/image.jpg', 'rb').read()
file_name = storage.save('image.jpg', file)


class ResourceFactory(ExtendedFactory):
    class Meta:
        model = Resource

    name = factory.Sequence(lambda n: "Resouce #%s" % n)
    description = factory.Sequence(lambda n: "Resource #%s description" % n)
    file = file_name
    original_file = 'image.jpg'
    contributor = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)
