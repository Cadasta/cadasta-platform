import os
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from core.tests.base_test_case import UserTestCase
from organization.tests.factories import ProjectFactory
from accounts.tests.factories import UserFactory

from ..models import Resource

from buckets.test.utils import ensure_dirs
from buckets.test.storage import FakeS3Storage
path = os.path.dirname(settings.BASE_DIR)

ensure_dirs()
storage = FakeS3Storage()
file = open(path + '/resources/tests/files/image.jpg', 'rb')
file_name = storage.save('image.jpg', file)


class ResourceModelTest(UserTestCase):
    def test_project_resource(self):
        project = ProjectFactory.create()
        user = UserFactory.create()

        resource = Resource.objects.create(name='Re',
                                           file=file_name,
                                           content_object=project,
                                           contributor=user,
                                           project=project)
        assert resource.name == 'Re'
        assert resource.content_objects.count() == 1
        assert resource.mime_type == 'image/jpeg'
        content_object = resource.content_objects.first()
        assert content_object.object_id == project.id
        assert content_object.content_type == ContentType.objects.get(
            app_label='organization', model='project')
