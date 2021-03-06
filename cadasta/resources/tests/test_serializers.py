import pytest
import os
from django.test import TestCase
from django.conf import settings
from rest_framework.serializers import ValidationError

from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from core.tests.utils.files import make_dirs  # noqa
from core.messages import SANITIZE_ERROR
from organization.tests.factories import ProjectFactory
from accounts.tests.factories import UserFactory

from .factories import ResourceFactory
from ..serializers import ResourceSerializer


@pytest.mark.usefixtures('make_dirs')
class ResourceSerializerTest(UserTestCase, FileStorageTestCase, TestCase):
    def test_serialize_fields(self):
        resource = ResourceFactory.create()
        serializer = ResourceSerializer(resource)

        serialized_resource = serializer.data

        assert serialized_resource['id'] == resource.id
        assert serialized_resource['name'] == resource.name
        assert serialized_resource['description'] == resource.description
        assert serialized_resource['file'] == resource.file.url

    def test_create_project_resource(self):
        file = self.get_file('/resources/tests/files/image.jpg', 'rb')
        file_name = self.storage.save('resources/image.jpg', file.read())
        file.close()

        project = ProjectFactory.create()
        user = UserFactory.create()
        data = {
            'name': 'New resource',
            'description': '',
            'file': file_name,
            'original_file': 'image.png',
            'mime_type': 'image/jpeg'
        }
        serializer = ResourceSerializer(
            data=data,
            context={'content_object': project,
                     'contributor': user,
                     'project_id': project.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        assert project.resources.count() == 1
        assert project.resources.first().name == data['name']
        assert project.resources.first().contributor == user
        assert os.path.isfile(os.path.join(
            settings.MEDIA_ROOT, 's3/uploads/resources/image-128x128.jpg')
        )

    def test_create_project_resource_without_mime_type(self):
        file = self.get_file('/resources/tests/files/text.txt', 'rb')
        file_name = self.storage.save('resources/text.txt', file.read())
        file.close()

        project = ProjectFactory.create()
        user = UserFactory.create()
        data = {
            'name': 'New resource',
            'description': '',
            'file': file_name,
            'original_file': 'text.txt'
        }
        serializer = ResourceSerializer(
            data=data,
            context={'content_object': project,
                     'contributor': user,
                     'project_id': project.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        assert project.resources.count() == 1
        assert project.resources.first().name == data['name']
        assert project.resources.first().contributor == user
        assert os.path.isfile(os.path.join(
            settings.MEDIA_ROOT, 's3/uploads/resources/text-128x128.txt')
        ) is False

    def test_assign_existing_resource(self):
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

    def test_assign_existing_resource_that_does_not_exist(self):
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

    def test_sanitize_string(self):
        file = self.get_file('/resources/tests/files/image.jpg', 'rb')
        file_name = self.storage.save('image.jpg', file.read())
        file.close()

        project = ProjectFactory.create()
        user = UserFactory.create()
        data = {
            'name': 'New resource',
            'description': '<Description>',
            'file': file_name,
            'original_file': 'image.png'
        }
        serializer = ResourceSerializer(
            data=data,
            context={'content_object': project,
                     'contributor': user,
                     'project_id': project.id})
        assert serializer.is_valid() is False
        assert SANITIZE_ERROR in serializer.errors['description']
