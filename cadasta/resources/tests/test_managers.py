import os
import pytest
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from core.tests.utils.cases import UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from organization.tests.factories import ProjectFactory
from accounts.tests.factories import UserFactory

from ..models import Resource

from buckets.test.storage import FakeS3Storage
path = os.path.dirname(settings.BASE_DIR)


@pytest.mark.usefixtures('make_dirs')
class ResourceModelTest(UserTestCase, TestCase):
    def test_project_resource(self):
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb').read()
        file_name = storage.save('resources/image.jpg', file)

        project = ProjectFactory.create()
        user = UserFactory.create()

        resource = Resource.objects.create(name='Re',
                                           file=file_name,
                                           content_object=project,
                                           contributor=user,
                                           project=project,
                                           mime_type='image/jpeg')
        assert resource.name == 'Re'
        assert resource.content_objects.count() == 1
        assert resource.mime_type == 'image/jpeg'
        content_object = resource.content_objects.first()
        assert content_object.object_id == project.id
        assert content_object.content_type == ContentType.objects.get(
            app_label='organization', model='project')
