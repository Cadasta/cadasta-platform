import pytest
from django.test import TestCase
from rest_framework.serializers import ValidationError

from spatial import serializers
from spatial.tests.factories import SpatialUnitFactory
from spatial.models import SpatialUnit
from organization.tests.factories import ProjectFactory


class SpatialUnitSerializerTest(TestCase):
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

    def test_project_detail_not_serialized(self):
        project = ProjectFactory.create()
        spatial_data = SpatialUnitFactory.create(project=project)
        serializer = serializers.SpatialUnitSerializer(spatial_data)
        assert 'description' not in serializer.data['properties']['project']

    def test_create_without_name(self):
        project = ProjectFactory.create()
        spatial_data = {
            'properties': {
                'name': '',
                'project': project
            }
        }

        serializer = serializers.SpatialUnitSerializer(
            data=spatial_data,
            context={'project': project}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_update_spatial_unit(self):
        project = ProjectFactory.create()
        su = SpatialUnitFactory.create(name='Test Spatial Unit',
                                       project=project)
        spatial_data = {
            'properties': {
                'name': 'Updated Spatial Unit',
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
        assert su_update.name == 'Updated Spatial Unit'

    def test_update_spatial_unit_fails(self):
        project = ProjectFactory.create()
        su = SpatialUnitFactory.create(name='Test Spatial Unit',
                                       project=project)
        spatial_data = {
            'properties': {
                'name': ''
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
        su = SpatialUnitFactory.create(name='Test Spatial Unit',
                                       project=project)
        ProjectFactory.create(name='New Project')
        spatial_data = {
            'properties': {
                'project': 'something'
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
        data = serializer.data['properties']
        assert data['project']['name'] != 'New Project'


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
