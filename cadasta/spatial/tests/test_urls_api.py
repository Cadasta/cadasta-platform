from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from core.tests.utils.urls import version_ns, version_url

from ..views import api
from party.views.api import RelationshipList


class SpatialUrlTest(TestCase):

    def test_project_spatial_unit_list(self):
        actual = reverse(
            version_ns('spatial:list'),
            kwargs={
                'organization': 'habitat',
                'project': '123abc',
            }
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/spatial/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/spatial/'))
        assert resolved.func.__name__ == api.SpatialUnitList.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'

    def test_project_spatial_unit_detail(self):
        actual = reverse(
            version_ns('spatial:detail'),
            kwargs={
                'organization': 'habitat',
                'project': '123abc',
                'location': '123456123456123456123456',
            }
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/'
            'spatial/123456123456123456123456/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/'
            'spatial/123456123456123456123456/'))
        assert resolved.func.__name__ == api.SpatialUnitDetail.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
        assert resolved.kwargs['location'] == '123456123456123456123456'

    def test_project_spatial_unit_relationships_list(self):
        actual = reverse(
            version_ns('spatial:rel_list'),
            kwargs={
                'organization': 'habitat',
                'project': '123abc',
                'location': '123456123456123456123456',
            }
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/'
            'spatial/123456123456123456123456/relationships/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/'
            'spatial/123456123456123456123456/relationships/'))
        assert resolved.func.__name__ == RelationshipList.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
        assert resolved.kwargs['location'] == '123456123456123456123456'

    def test_spatial_unit_resource_list(self):
        actual = reverse(
            version_ns('spatial:resource_list'),
            kwargs={
                'organization': 'habitat',
                'project': '123abc',
                'location': '123456123456123456123456',
            }
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/'
            'spatial/123456123456123456123456/resources/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/spatial/'
            '123456123456123456123456/resources/'))
        assert resolved.func.__name__ == api.SpatialUnitResourceList.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
        assert resolved.kwargs['location'] == '123456123456123456123456'

    def test_spatial_unit_resource_detail(self):
        actual = reverse(
            version_ns('spatial:resource_detail'),
            kwargs={
                'organization': 'habitat',
                'project': '123abc',
                'location': '123456123456123456123456',
                'resource': '12340293170489127699348'
            }
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/'
            'spatial/123456123456123456123456/'
            'resources/12340293170489127699348/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/'
            'spatial/123456123456123456123456/'
            'resources/12340293170489127699348/'))
        assert (resolved.func.__name__ ==
                api.SpatialUnitResourceDetail.__name__)
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
        assert resolved.kwargs['location'] == '123456123456123456123456'
        assert resolved.kwargs['resource'] == '12340293170489127699348'
