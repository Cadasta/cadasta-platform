import os

from django.test import TestCase
from django.conf import settings

from .factories import ResourceFactory
from ..models import ContentObject, Resource, create_thumbnails

from buckets.test.utils import ensure_dirs
from buckets.test.storage import FakeS3Storage
path = os.path.dirname(settings.BASE_DIR)


class ResourceTest(TestCase):
    def test_file_name_property(self):
        resource = Resource(file='http://example.com/dir/filename.txt')
        assert resource.file_name == 'filename.txt'

    def test_file_type_property(self):
        resource = Resource(file='http://example.com/dir/filename.txt')
        assert resource.file_type == 'txt'

    def test_thumbnail(self):
        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.jpg',
            mime_type='image/jpg'
        )
        assert (resource.thumbnail ==
                'http://example.com/dir/filename-128x128.jpg')

        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.pdf',
            mime_type='application/pdf'
        )
        assert (resource.thumbnail == '')

    def test_num_entities(self):
        resource = ResourceFactory.create()
        ContentObject.objects.create(resource=resource,
                                     content_object=resource.project)
        ContentObject.objects.create(resource=resource,
                                     content_object=resource.project)
        assert resource.num_entities == 2

    def test_register_file_version(self):
        ensure_dirs()
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb')
        file_name = storage.save('thumb_new.jpg', file)
        resource = ResourceFactory.create()

        resource.file = file_name
        resource.save()

        assert resource.file.url == file_name
        assert len(resource.file_versions) == 1

    def test_create_thumbnail(self):
        ensure_dirs()
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb')
        file_name = storage.save('thumb_test.jpg', file)
        resource = ResourceFactory.build(file=file_name)

        create_thumbnails(Resource, resource, True)
        assert os.path.isfile(os.path.join(settings.MEDIA_ROOT,
                              's3/uploads/thumb_test-128x128.jpg'))
