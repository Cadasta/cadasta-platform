import os

import pytest

from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from core.tests.utils.files import make_dirs  # noqa
from django.conf import settings
from django.test import TestCase
from django.utils.translation import gettext as _

from organization.tests.factories import ProjectFactory
from ..exceptions import InvalidGPXFile
from ..models import (ContentObject, Resource, SpatialResource,
                      create_spatial_resource)
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

    def test_num_entities(self):
        resource = ResourceFactory.create()
        ContentObject.objects.create(resource=resource,
                                     content_object=resource.project)
        ContentObject.objects.create(resource=resource,
                                     content_object=resource.project)
        assert resource.num_entities == 2

    def test_register_file_version(self):
        file = self.get_file('/resources/tests/files/image.jpg', 'rb')
        file_name = self.storage.save('resources/thumb_new.jpg', file.read())
        file.close()
        resource = ResourceFactory.create()

        resource.file = file_name
        resource.save()

        assert resource.file.url == file_name
        assert len(resource.file_versions) == 1

    def test_create_spatial_resource(self):
        file = self.get_file('/resources/tests/files/deramola.xml', 'rb')
        file_name = self.storage.save('resources/deramola.xml', file.read())
        file.close()
        resource = ResourceFactory.create(
            file=file_name, mime_type='text/xml')
        assert os.path.isfile(os.path.join(
            settings.MEDIA_ROOT, 's3/uploads/resources/deramola.xml')
        )
        spatial_resources = resource.spatial_resources.all()
        assert spatial_resources.count() == 1
        resource = spatial_resources[0]
        assert len(resource.geom[0]) == 18
        assert spatial_resources[0].name == 'waypoints'
        assert spatial_resources[0].attributes == {}

    def test_invalid_gpx_mime_type(self):
        file = self.get_file('/resources/tests/files/mp3.xml', 'rb')
        file_name = self.storage.save('resources/mp3.xml', file.read())
        file.close()
        resource = ResourceFactory.build(
            file=file_name, mime_type='text/xml')
        assert os.path.isfile(os.path.join(
            settings.MEDIA_ROOT, 's3/uploads/resources/mp3.xml')
        )
        with pytest.raises(InvalidGPXFile) as e:
            create_spatial_resource(Resource, resource, True)

        assert str(e.value) == _("Invalid GPX mime type: audio/mpeg")

    def test_invalid_gpx_file(self):
        file = self.get_file('/resources/tests/files/invalidgpx.xml', 'rb')
        file_name = self.storage.save('resources/invalidgpx.xml', file.read())
        file.close()
        resource = ResourceFactory.build(
            file=file_name, mime_type='application/xml')
        assert os.path.isfile(os.path.join(
            settings.MEDIA_ROOT, 's3/uploads/resources/invalidgpx.xml')
        )
        with pytest.raises(InvalidGPXFile)as e:
            create_spatial_resource(Resource, resource, True)
        assert str(e.value) == _("Error parsing GPX file: no geometry found.")
        assert Resource.objects.all().count() == 0

    def test_handle_invalid_xml_version(self):
        file = self.get_file(
            '/resources/tests/files/invalid_xml_version.gpx', 'rb')
        file_name = self.storage.save(
            'resources/invalid_xml_version.gpx', file.read())
        file.close()
        resource = ResourceFactory.build(
            file=file_name, mime_type='application/xml')
        assert os.path.isfile(os.path.join(
            settings.MEDIA_ROOT,
            's3/uploads/resources/invalid_xml_version.gpx')
        )
        with pytest.raises(InvalidGPXFile)as e:
            create_spatial_resource(Resource, resource, True)
        assert str(e.value)[:16] == _("Invalid GPX file")
        assert Resource.objects.all().count() == 0


@pytest.mark.usefixtures('make_dirs')
@pytest.mark.usefixtures('clear_temp')
class SpatialResourceTest(UserTestCase, FileStorageTestCase, TestCase):
    def test_repr(self):
        res = ResourceFactory.build(id='abc123')
        resource = SpatialResourceFactory.build(id='abc123', resource=res)
        assert repr(resource) == '<SpatialResource id=abc123 resource=abc123>'

    def test_spatial_resource(self):
        file = self.get_file('/resources/tests/files/tracks.gpx', 'rb')
        file_name = self.storage.save('resources/tracks_test.gpx', file.read())
        file.close()
        resource = ResourceFactory.create(
            file=file_name, mime_type='text/xml')
        spatial_resource = SpatialResourceFactory.create(resource=resource)
        assert spatial_resource.project.pk == resource.project.pk
        assert spatial_resource.archived == resource.archived

    def test_spatial_resource_routes_and_tracks(self):
        file = self.get_file('/resources/tests/files/routes_tracks.gpx', 'rb')
        file_name = self.storage.save(
            'resources/routes_tracks.gpx', file.read())
        file.close()
        resource = ResourceFactory.create(
            file=file_name, mime_type='text/xml')
        assert SpatialResource.objects.filter(resource=resource).count() == 2
