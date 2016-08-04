import os
import pytest
from django.conf import settings
from django.test import TestCase
from rest_framework.serializers import ValidationError

from core.tests.utils.cases import UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from organization.tests.factories import ProjectFactory
from accounts.tests.factories import UserFactory

from .factories import ResourceFactory
from ..serializers import ResourceSerializer

from buckets.test.storage import FakeS3Storage
path = os.path.dirname(settings.BASE_DIR)


@pytest.mark.usefixtures('make_dirs')
class ResourceSerializerTest(UserTestCase, TestCase):
    def test_serialize_fields(self):
        resource = ResourceFactory.create()
        serializer = ResourceSerializer(resource)

        serialized_resource = serializer.data

        assert serialized_resource['id'] == resource.id
        assert serialized_resource['name'] == resource.name
        assert serialized_resource['description'] == resource.description
        assert serialized_resource['file'] == resource.file.url

    def test_create_project_resource(self):
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb').read()
        file_name = storage.save('image.jpg', file)

        project = ProjectFactory.create()
        user = UserFactory.create()
        data = {
            'name': 'New resource',
            'description': '',
            'file': file_name,
            'original_file': 'image.png'
        }
        serializer = ResourceSerializer(
            data=data,
            context={'content_object': project,
                     'contributor': user,
                     'project_id': project.id})
        serializer.is_valid()
        serializer.save()

        assert project.resources.count() == 1
        assert project.resources.first().name == data['name']
        assert project.resources.first().contributor == user

    def test_assign_exisiting_resource(self):
        project = ProjectFactory.create()
        resource = ResourceFactory.create()
        data = {'id': resource.id}
        serializer = ResourceSerializer(
            data=data,
            context={'content_object': project}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        assert project.resources.count() == 1

    def test_assign_exisiting_resource_that_does_not_exist(self):
        project = ProjectFactory.create()
        data = {'id': 'askldh89yashd89ahsd'}
        serializer = ResourceSerializer(
            data=data,
            context={'content_object': project}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert serializer.is_valid() is False
        assert serializer.errors['id'] == 'Resource not found'
        assert project.resources.count() == 0
