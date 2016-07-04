from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from ..views import default


class LocationsUrlsTest(TestCase):
    def test_locations_list(self):
        url = reverse('locations:list',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'locations/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/locations/')
        assert resolved.func.__name__ == default.LocationsList.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_locations_add(self):
        url = reverse('locations:add',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'locations/new/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/'
            'locations/new/')
        assert resolved.func.__name__ == default.LocationsAdd.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_locations_detail(self):
        url = reverse('locations:detail',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'location': 'abc123'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'locations/abc123/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/'
            'locations/abc123/')
        assert resolved.func.__name__ == default.LocationDetail.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['location'] == 'abc123'

    def test_locations_edit(self):
        url = reverse('locations:edit',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'location': 'abc123'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'locations/abc123/edit/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/'
            'locations/abc123/edit/')
        assert resolved.func.__name__ == default.LocationEdit.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['location'] == 'abc123'

    def test_locations_delete(self):
        url = reverse('locations:delete',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'location': 'abc123'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'locations/abc123/delete/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/'
            'locations/abc123/delete/')
        assert resolved.func.__name__ == default.LocationDelete.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['location'] == 'abc123'


class LocationsResourcesUrlsTest(TestCase):
    def test_resource_add_from_lib(self):
        url = reverse('locations:resource_add',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'location': 'abc123'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'locations/abc123/resources/add/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/locations/'
            'abc123/resources/add/')
        assert resolved.func.__name__ == default.LocationResourceAdd.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['location'] == 'abc123'

    def test_resource_add_new(self):
        url = reverse('locations:resource_new',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'location': 'abc123'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'locations/abc123/resources/new/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/locations/'
            'abc123/resources/new/')
        assert resolved.func.__name__ == default.LocationResourceNew.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['location'] == 'abc123'


class TenureRelationshipAddUrlsTest(TestCase):
    def test_relationship_new(self):
        url = reverse('locations:relationship_add',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'location': 'abc123'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'locations/abc123/relationships/new/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/locations/'
            'abc123/relationships/new/')
        assert (resolved.func.__name__ ==
                default.TenureRelationshipAdd.__name__)
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['location'] == 'abc123'
