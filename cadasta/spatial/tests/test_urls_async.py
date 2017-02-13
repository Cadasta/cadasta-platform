from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from ..views import async


class LocationsUrlsTest(TestCase):
    def test_locations_add(self):
        url = reverse('async:spatial:add',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert (url ==
                '/async/organizations/org-slug/projects/proj-slug/records/'
                'location/new/')

        resolved = resolve(
            '/async/organizations/org-slug/projects/proj-slug/records/'
            'location/new/')
        assert resolved.func.__name__ == async.LocationsAdd.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_locations_detail(self):
        url = reverse('async:spatial:detail',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'location': 'abc123'})
        assert (url ==
                '/async/organizations/org-slug/projects/proj-slug/records/'
                'location/abc123/')

        resolved = resolve(
            '/async/organizations/org-slug/projects/proj-slug/records/'
            'location/abc123/')
        assert resolved.func.__name__ == async.LocationDetail.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['location'] == 'abc123'

    def test_locations_edit(self):
        url = reverse('async:spatial:edit',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'location': 'abc123'})
        assert (url ==
                '/async/organizations/org-slug/projects/proj-slug/records/'
                'location/abc123/edit/')

        resolved = resolve(
            '/async/organizations/org-slug/projects/proj-slug/records/'
            'location/abc123/edit/')
        assert resolved.func.__name__ == async.LocationEdit.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['location'] == 'abc123'

    def test_locations_delete(self):
        url = reverse('async:spatial:delete',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'location': 'abc123'})
        assert (url ==
                '/async/organizations/org-slug/projects/proj-slug/records/'
                'location/abc123/delete/')

        resolved = resolve(
            '/async/organizations/org-slug/projects/proj-slug/records/'
            'location/abc123/delete/')
        assert resolved.func.__name__ == async.LocationDelete.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['location'] == 'abc123'


class LocationsResourcesUrlsTest(TestCase):
    def test_resource_add_from_lib(self):
        url = reverse('async:spatial:resource_add',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'location': 'abc123'})
        assert (url ==
                '/async/organizations/org-slug/projects/proj-slug/records/'
                'location/abc123/resources/add/')

        resolved = resolve(
            '/async/organizations/org-slug/projects/proj-slug/records/'
            'location/abc123/resources/add/')
        assert resolved.func.__name__ == async.LocationResourceAdd.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['location'] == 'abc123'

    def test_resource_add_new(self):
        url = reverse('async:spatial:resource_new',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'location': 'abc123'})
        assert (url ==
                '/async/organizations/org-slug/projects/proj-slug/records/'
                'location/abc123/resources/new/')

        resolved = resolve(
            '/async/organizations/org-slug/projects/proj-slug/records/'
            'location/abc123/resources/new/')
        assert resolved.func.__name__ == async.LocationResourceNew.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['location'] == 'abc123'


class TenureRelationshipAddUrlsTest(TestCase):
    def test_relationship_new(self):
        url = reverse('async:spatial:relationship_add',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'location': 'abc123'})
        assert (url ==
                '/async/organizations/org-slug/projects/proj-slug/records/'
                'location/abc123/relationships/new/')

        resolved = resolve(
            '/async/organizations/org-slug/projects/proj-slug/records/'
            'location/abc123/relationships/new/')
        assert (resolved.func.__name__ ==
                async.TenureRelationshipAdd.__name__)
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['location'] == 'abc123'


class SpatialUrlTest(TestCase):
    def test_project_spatial_unit_tiled(self):
        url = reverse('async:spatial:tiled',
                      kwargs={
                        'organization': 'habitat',
                        'project': '123abc',
                        'x': 0,
                        'y': 0,
                        'z': 0,
                      })
        assert (url ==
                '/async/organizations/habitat/projects/123abc/'
                'spatial/tiled/0/0/0/')

        resolved = resolve(
            '/async/organizations/habitat/projects/123abc/'
            'spatial/tiled/0/0/0/')
        assert resolved.func.__name__ == async.SpatialUnitTiles.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
