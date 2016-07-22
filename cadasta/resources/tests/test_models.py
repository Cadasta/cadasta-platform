import pytest
import os

from django.conf import settings

from core.tests.base_test_case import UserTestCase
from core.tests.util import make_dirs  # noqa
from .factories import ResourceFactory
from .utils import clear_temp  # noqa
from ..models import ContentObject, Resource, create_thumbnails

from buckets.test.storage import FakeS3Storage
path = os.path.dirname(settings.BASE_DIR)


@pytest.mark.usefixtures('make_dirs')
@pytest.mark.usefixtures('clear_temp')
class ResourceTest(UserTestCase):
    def test_file_name_property(self):
        resource = Resource(file='http://example.com/dir/filename.txt')
        assert resource.file_name == 'filename.txt'

    def test_file_type_property(self):
        resource = Resource(file='http://example.com/dir/filename.txt')
        assert resource.file_type == 'txt'

    def test_thumbnail_img(self):
        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.jpg',
            mime_type='image/jpg'
        )
        assert (resource.thumbnail ==
                'http://example.com/dir/filename-128x128.jpg')

    def test_thumbnail_pdf(self):
        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.pdf',
            mime_type='application/pdf'
        )
        assert (resource.thumbnail ==
                'https://s3-us-west-2.amazonaws.com/cadasta-platformprod-'
                'bucket/icons/pdf.png')

    def test_thumbnail_mp3(self):
        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.mp3',
            mime_type='audio/mpeg3'
        )
        assert (resource.thumbnail ==
                'https://s3-us-west-2.amazonaws.com/cadasta-platformprod-'
                'bucket/icons/mp3.png')

        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.mp3',
            mime_type='audio/x-mpeg-3'
        )
        assert (resource.thumbnail ==
                'https://s3-us-west-2.amazonaws.com/cadasta-platformprod-'
                'bucket/icons/mp3.png')

        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.mp3',
            mime_type='video/mpeg'
        )
        assert (resource.thumbnail ==
                'https://s3-us-west-2.amazonaws.com/cadasta-platformprod-'
                'bucket/icons/mp3.png')

        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.mp3',
            mime_type='video/x-mpeg'
        )
        assert (resource.thumbnail ==
                'https://s3-us-west-2.amazonaws.com/cadasta-platformprod-'
                'bucket/icons/mp3.png')

    def test_thumbnail_mp4(self):
        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.mp4',
            mime_type='video/mp4'
        )
        assert (resource.thumbnail ==
                'https://s3-us-west-2.amazonaws.com/cadasta-platformprod-'
                'bucket/icons/mp4.png')

    def test_thumbnail_doc(self):
        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.doc',
            mime_type='application/msword'
        )
        assert (resource.thumbnail ==
                'https://s3-us-west-2.amazonaws.com/cadasta-platformprod-'
                'bucket/icons/doc.png')

    def test_thumbnail_docx(self):
        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.doc',
            mime_type=('application/vnd.openxmlformats-officedocument.'
                       'wordprocessingml.document')
        )
        assert (resource.thumbnail ==
                'https://s3-us-west-2.amazonaws.com/cadasta-platformprod-'
                'bucket/icons/docx.png')

    def test_thumbnail_xls(self):
        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.doc',
            mime_type='application/msexcel'
        )
        assert (resource.thumbnail ==
                'https://s3-us-west-2.amazonaws.com/cadasta-platformprod-'
                'bucket/icons/xls.png')

        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.doc',
            mime_type='application/vnd.ms-excel'
        )
        assert (resource.thumbnail ==
                'https://s3-us-west-2.amazonaws.com/cadasta-platformprod-'
                'bucket/icons/xls.png')

    def test_thumbnail_xlsx(self):
        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.doc',
            mime_type=('application/vnd.openxmlformats-officedocument'
                       '.spreadsheetml.sheet')
        )
        assert (resource.thumbnail ==
                'https://s3-us-west-2.amazonaws.com/cadasta-platformprod-'
                'bucket/icons/xlsx.png')

    def test_thumbnail_other(self):
        resource = ResourceFactory.build(
            file='http://example.com/dir/filename.pdf',
            mime_type='application/other'
        )
        assert resource.thumbnail == ''

    def test_num_entities(self):
        resource = ResourceFactory.create()
        ContentObject.objects.create(resource=resource,
                                     content_object=resource.project)
        ContentObject.objects.create(resource=resource,
                                     content_object=resource.project)
        assert resource.num_entities == 2

    def test_register_file_version(self):
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb').read()
        file_name = storage.save('resources/thumb_new.jpg', file)
        resource = ResourceFactory.create()

        resource.file = file_name
        resource.save()

        assert resource.file.url == file_name
        assert len(resource.file_versions) == 1

    def test_create_thumbnail(self):
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb').read()
        file_name = storage.save('resources/thumb_test.jpg', file)
        resource = ResourceFactory.build(file=file_name,
                                         mime_type='image/jpeg')

        create_thumbnails(Resource, resource, True)
        assert os.path.isfile(os.path.join(settings.MEDIA_ROOT,
                              's3/uploads/resources/thumb_test-128x128.jpg'))
