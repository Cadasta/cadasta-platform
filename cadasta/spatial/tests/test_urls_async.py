from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from ..views import async


class SpatialUrlTest(TestCase):

    def test_project_spatial_unit_list(self):
        actual = reverse('async:spatial:list',
                         kwargs={
                            'organization': 'habitat',
                            'project': '123abc',
                         })
        expected = '/async/organizations/habitat/projects/123abc/spatial/'
        assert actual == expected

        resolved = resolve(
            '/async/organizations/habitat/projects/123abc/spatial/')
        assert resolved.func.__name__ == async.SpatialUnitList.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
