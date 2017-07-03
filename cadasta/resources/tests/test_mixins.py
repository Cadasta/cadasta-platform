import pytest
import os
from django.conf import settings
from django.db.models import Model
from django.test import TestCase
from buckets.fields import S3FileField

from ..mixins import ResourceModelMixin, ResourceThumbnailMixin
from .factories import ResourceFactory
from ..models import Resource
from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from core.tests.utils.files import make_dirs  # noqa
from .utils import clear_temp  # noqa


class ResourceModel(ResourceModelMixin, Model):
    class Meta:
        app_label = 'core'


class ResourceThumbnailModel(ResourceThumbnailMixin, Model):
    class Meta:
        app_label = 'core'
    file = S3FileField(upload_to='resources', null=True, blank=True)

    @property
    def mime_type(self):
        return 'image/*'


@pytest.mark.usefixtures('make_dirs')
class ResourceModelMixinTest(UserTestCase, TestCase):
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


@pytest.mark.usefixtures('make_dirs')
@pytest.mark.usefixtures('clear_temp')
class ResourceThumbnailMixinTest(UserTestCase, FileStorageTestCase, TestCase):

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
                    'https://s3-us-west-2.amazonaws.com/cadasta-resources'
                    '/icons/pdf.png')

        def test_thumbnail_mp3(self):
            resource = ResourceFactory.build(
                file='http://example.com/dir/filename.mp3',
                mime_type='audio/mpeg3'
            )
            assert (resource.thumbnail ==
                    'https://s3-us-west-2.amazonaws.com/cadasta-resources'
                    '/icons/mp3.png')

            resource = ResourceFactory.build(
                file='http://example.com/dir/filename.mp3',
                mime_type='audio/x-mpeg-3'
            )
            assert (resource.thumbnail ==
                    'https://s3-us-west-2.amazonaws.com/cadasta-resources'
                    '/icons/mp3.png')

            resource = ResourceFactory.build(
                file='http://example.com/dir/filename.mp3',
                mime_type='video/mpeg'
            )
            assert (resource.thumbnail ==
                    'https://s3-us-west-2.amazonaws.com/cadasta-resources'
                    '/icons/mp3.png')

            resource = ResourceFactory.build(
                file='http://example.com/dir/filename.mp3',
                mime_type='video/x-mpeg'
            )
            assert (resource.thumbnail ==
                    'https://s3-us-west-2.amazonaws.com/cadasta-resources'
                    '/icons/mp3.png')

        def test_thumbnail_mp4(self):
            resource = ResourceFactory.build(
                file='http://example.com/dir/filename.mp4',
                mime_type='video/mp4'
            )
            assert (resource.thumbnail ==
                    'https://s3-us-west-2.amazonaws.com/cadasta-resources'
                    '/icons/mp4.png')

        def test_thumbnail_doc(self):
            resource = ResourceFactory.build(
                file='http://example.com/dir/filename.doc',
                mime_type='application/msword'
            )
            assert (resource.thumbnail ==
                    'https://s3-us-west-2.amazonaws.com/cadasta-resources'
                    '/icons/doc.png')

        def test_thumbnail_docx(self):
            resource = ResourceFactory.build(
                file='http://example.com/dir/filename.doc',
                mime_type=('application/vnd.openxmlformats-officedocument.'
                           'wordprocessingml.document')
            )
            assert (resource.thumbnail ==
                    'https://s3-us-west-2.amazonaws.com/cadasta-resources'
                    '/icons/docx.png')

        def test_thumbnail_xls(self):
            resource = ResourceFactory.build(
                file='http://example.com/dir/filename.doc',
                mime_type='application/msexcel'
            )
            assert (resource.thumbnail ==
                    'https://s3-us-west-2.amazonaws.com/cadasta-resources'
                    '/icons/xls.png')

            resource = ResourceFactory.build(
                file='http://example.com/dir/filename.doc',
                mime_type='application/vnd.ms-excel'
            )
            assert (resource.thumbnail ==
                    'https://s3-us-west-2.amazonaws.com/cadasta-resources'
                    '/icons/xls.png')

        def test_thumbnail_xlsx(self):
            resource = ResourceFactory.build(
                file='http://example.com/dir/filename.doc',
                mime_type=('application/vnd.openxmlformats-officedocument'
                           '.spreadsheetml.sheet')
            )
            assert (resource.thumbnail ==
                    'https://s3-us-west-2.amazonaws.com/cadasta-resources'
                    '/icons/xlsx.png')

        def test_thumbnail_xml(self):
            resource = ResourceFactory.build(
                file='http://example.com/dir/filename.gpx',
                mime_type=('text/xml'))
            assert (resource.thumbnail ==
                    'https://s3-us-west-2.amazonaws.com/cadasta-resources'
                    '/icons/xml.png')

        def test_thumbnail_other(self):
            resource = ResourceFactory.build(
                file='http://example.com/dir/filename.pdf',
                mime_type='application/other'
            )
            assert resource.thumbnail == ''

        def test_create_thumbnail(self):
            file = self.get_file('/resources/tests/files/image.jpg', 'rb')
            file_name = self.storage.save(
                'resources/thumb_test.jpg', file.read())
            contributor = UserFactory.create()
            resource = ResourceFactory.create(file=file_name,
                                              mime_type='image/jpeg',
                                              contributor=contributor)
            resource.save()
            assert os.path.isfile(
                os.path.join(
                    settings.MEDIA_ROOT,
                    's3/uploads/resources/thumb_test-128x128.jpg'
                )
            )

        def test_create_no_thumbnail_non_images(self):
            file = self.get_file('/resources/tests/files/text.txt', 'rb')
            file_name = self.storage.save('resources/text.txt', file.read())
            contributor = UserFactory.create()
            resource = ResourceFactory.create(file=file_name,
                                              mime_type='text/plain',
                                              contributor=contributor)
            resource.save()
            assert os.path.isfile(os.path.join(
                settings.MEDIA_ROOT, 's3/uploads/resources/text-128x128.txt')
            ) is False

        def test_get_mime(self):
            resource = ResourceThumbnailModel()
            assert resource._get_mime() == 'image/*'

        def test_missing_mime_type_attribute(self):
            del ResourceThumbnailModel.mime_type
            resource = ResourceThumbnailModel()
            with pytest.raises(AttributeError) as e:
                resource._get_mime()
            assert str(e.value) == "No 'mime_type' attribute found."
