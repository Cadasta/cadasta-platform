import pytest
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from rest_framework.serializers import ValidationError
from jsonattrs.models import Attribute, AttributeType, Schema

from core.tests.utils.cases import UserTestCase
from spatial import serializers
from spatial.tests.factories import SpatialUnitFactory
from spatial.models import SpatialUnit
from organization.tests.factories import ProjectFactory


class SpatialUnitSerializerTest(UserTestCase, TestCase):
    def test_geojson_serialization(self):
        spatial_data = SpatialUnitFactory.create()
        serializer = serializers.SpatialUnitSerializer(spatial_data)
        assert serializer.data['type'] == 'Feature'
        assert 'geometry' in serializer.data
        assert 'properties' in serializer.data

    def test_project_is_set(self):
        project = ProjectFactory.create()
        spatial_data = {
            'properties': {
                'name': 'Spatial',
                'project': project
            }
        }
        serializer = serializers.SpatialUnitSerializer(
            data=spatial_data,
            context={'project': project}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        spatial_instance = serializer.instance
        assert spatial_instance.project == project

    def test_update_spatial_unit(self):
        project = ProjectFactory.create()
        su = SpatialUnitFactory.create(type='BU',
                                       project=project)
        spatial_data = {
            'properties': {
                'type': 'AP',
                'project': project
            }
        }
        serializer = serializers.SpatialUnitSerializer(
            su,
            data=spatial_data,
            partial=True,
            context={'project': project}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        su_update = SpatialUnit.objects.get(id=su.id)
        assert su_update.type == 'AP'

    def test_update_spatial_unit_fails(self):
        project = ProjectFactory.create()
        su = SpatialUnitFactory.create(type='BU',
                                       project=project)
        spatial_data = {
            'properties': {
                'type': ''
            }
        }
        serializer = serializers.SpatialUnitSerializer(
            su,
            data=spatial_data,
            partial=True,
            context={'project': project}
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_update_spatial_unit_project_fails(self):
        project = ProjectFactory.create(name='Original Project')
        su = SpatialUnitFactory.create(project=project)
        new_project = ProjectFactory.create(name='New Project')
        spatial_data = {
            'properties': {
                'project': new_project
            }
        }
        serializer = serializers.SpatialUnitSerializer(
            su,
            data=spatial_data,
            partial=True,
            context={'project': project}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        su.refresh_from_db()
        assert su.project == project

    def test_invalid_attributes(self):
        project = ProjectFactory.create(name='Test Project')

        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema,
            name='notes',
            long_name='Notes',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='age',
            long_name='Homeowner Age',
            attr_type=AttributeType.objects.get(name='integer'),
            index=1, required=True, default=0
        )

        data = {
            'properties': {
                'type': 'AP',
                'project': project,
                'attributes': {
                    'notes': 'Blah',
                    'age': 'Ten'
                }
            }
        }

        serializer = serializers.SpatialUnitSerializer(
            data=data,
            context={'project': project}
        )
        assert serializer.is_valid() is False
        assert serializer.errors['attributes']


class SpatialUnitGeoJsonSerializerTest(TestCase):
    def test_serialize(self):
        location = SpatialUnitFactory.build(id='abc123')
        serializer = serializers.SpatialUnitGeoJsonSerializer(location)

        assert 'type' in serializer.data['properties']
        assert 'url' in serializer.data['properties']
        assert 'geometry' in serializer.data

    def test_get_url(self):
        location = SpatialUnitFactory.build(id='abc123')
        serializer = serializers.SpatialUnitGeoJsonSerializer(location)

        expected_url = ('/organizations/{o}/projects/{p}/records/'
                        'locations/{l}/'.format(
                            o=location.project.organization.slug,
                            p=location.project.slug,
                            l=location.id
                        ))

        assert serializer.get_url(location) == expected_url

    def test_get_type(self):
        location = SpatialUnitFactory.build(type='CB')
        serializer = serializers.SpatialUnitGeoJsonSerializer(location)
        assert serializer.get_type(location) == 'Community boundary'
