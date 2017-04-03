import os

import pytest

from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from core.tests.utils.files import make_dirs  # noqa
from django.conf import settings
from django.test import TestCase
from django.utils.translation import gettext as _

from accounts.tests.factories import UserFactory
from organization.tests.factories import ProjectFactory
from ..exceptions import InvalidGPXFile
from ..models import ContentObject, Resource, create_spatial_resource
from .factories import ResourceFactory, SpatialResourceFactory
from .utils import clear_temp  # noqa


@pytest.mark.usefixtures('make_dirs')
@pytest.mark.usefixtures('clear_temp')
class ResourceTest(UserTestCase, FileStorageTestCase, TestCase):

    def test_repr(self):
        project = ProjectFactory.build(slug='prj')
        resource = Resource(id='abc123', name='File',
                            file='http://example.com/test.txt',
                            project=project)
        assert repr(resource) == ('<Resource id=abc123 name=File'
                                  ' file=http://example.com/test.txt'
                                  ' project=prj>')

    def test_file_name_property(self):
        resource = Resource(file='http://example.com/dir/filename.txt')
        assert resource.file_name == 'filename.txt'

    def test_file_type_property(self):
        resource = Resource(file='http://example.com/dir/filename.txt')
        assert resource.file_type == 'txt'

    def test_ui_class_name(self):
        resource = ResourceFactory.create()
        assert resource.ui_class_name == "Resource"

    def test_get_absolute_url(self):
        resource = ResourceFactory.create()
        assert resource.get_absolute_url() == (
            '/organizations/{org}/projects/{prj}/'
            'resources/{id}/'.format(
                org=resource.project.organization.slug,
                prj=resource.project.slug,
                id=resource.id))

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

    def test_num_entities(self):
        resource = ResourceFactory.create()
        ContentObject.objects.create(resource=resource,
                                     content_object=resource.project)
        ContentObject.objects.create(resource=resource,
                                     content_object=resource.project)
        assert resource.num_entities == 2

    def test_register_file_version(self):
        file = self.get_file('/resources/tests/files/image.jpg', 'rb')
        file_name = self.storage.save('resources/thumb_new.jpg', file)
        resource = ResourceFactory.create()

        resource.file = file_name
        resource.save()

        assert resource.file.url == file_name
        assert len(resource.file_versions) == 1

    def test_create_thumbnail(self):
        file = self.get_file('/resources/tests/files/image.jpg', 'rb')
        file_name = self.storage.save('resources/thumb_test.jpg', file)
        contributor = UserFactory.create()
        resource = ResourceFactory.create(file=file_name,
                                          mime_type='image/jpeg',
                                          contributor=contributor)
        resource.save()
        assert os.path.isfile(os.path.join(
            settings.MEDIA_ROOT, 's3/uploads/resources/thumb_test-128x128.jpg')
        )

    def test_create_no_thumbnail_non_images(self):
        file = self.get_file('/resources/tests/files/text.txt', 'rb')
        file_name = self.storage.save('resources/text.txt', file)
        contributor = UserFactory.create()
        resource = ResourceFactory.create(file=file_name,
                                          mime_type='text/plain',
                                          contributor=contributor)
        resource.save()
        assert os.path.isfile(os.path.join(
            settings.MEDIA_ROOT, 's3/uploads/resources/text-128x128.txt')
        ) is False

    def test_create_spatial_resource(self):
        file = self.get_file('/resources/tests/files/deramola.xml', 'rb')
        file_name = self.storage.save('resources/deramola.xml', file)
        resource = ResourceFactory.create(
            file=file_name, mime_type='text/xml')
        assert os.path.isfile(os.path.join(
            settings.MEDIA_ROOT, 's3/uploads/resources/deramola.xml')
        )
        spatial_resources = resource.spatial_resources.all()
        assert spatial_resources.count() == 1
        geom = spatial_resources[0].geom
        assert len(geom) == 18
        assert spatial_resources[0].name == 'waypoints'
        assert spatial_resources[0].attributes == {}

    def test_invalid_gpx_mime_type(self):
        file = self.get_file('/resources/tests/files/mp3.xml', 'rb')
        file_name = self.storage.save('resources/mp3.xml', file)
        resource = ResourceFactory.build(
            file=file_name, mime_type='text/xml')
        assert os.path.isfile(os.path.join(
            settings.MEDIA_ROOT, 's3/uploads/resources/mp3.xml')
        )
        with pytest.raises(InvalidGPXFile) as e:
            create_spatial_resource(Resource, resource, True)

        assert str(e.value) == _('Invalid GPX mime type: audio/mpeg')

    def test_invalid_gpx_file(self):
        file = self.get_file('/resources/tests/files/invalidgpx.xml', 'rb')
        file_name = self.storage.save('resources/invalidgpx.xml', file)
        resource = ResourceFactory.build(
            file=file_name, mime_type='application/xml')
        assert os.path.isfile(os.path.join(
            settings.MEDIA_ROOT, 's3/uploads/resources/invalidgpx.xml')
        )
        with pytest.raises(InvalidGPXFile)as e:
            create_spatial_resource(Resource, resource, True)
        assert str(e.value) == _('Invalid GPX file')
        assert Resource.objects.all().count() == 0


class SpatialResourceTest(UserTestCase, FileStorageTestCase, TestCase):
    def test_repr(self):
        res = ResourceFactory.build(id='abc123')
        resource = SpatialResourceFactory.build(id='abc123', resource=res)
        assert repr(resource) == '<SpatialResource id=abc123 resource=abc123>'

    def test_spatial_resource(self):
        file = self.get_file('/resources/tests/files/tracks.gpx', 'rb')
        file_name = self.storage.save('resources/tracks_test.gpx', file)
        resource = ResourceFactory.create(
            file=file_name, mime_type='text/xml')
        spatial_resource = SpatialResourceFactory.create(resource=resource)
        assert spatial_resource.project.pk == resource.project.pk
        assert spatial_resource.archived == resource.archived
