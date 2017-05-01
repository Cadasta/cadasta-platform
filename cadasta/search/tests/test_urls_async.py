from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from ..views import async


class SearchUrlTest(TestCase):

    def test_search(self):
        actual = reverse('async:search:search',
                         kwargs={
                            'organization': 'habitat',
                            'project': '123',
                         })
        expected = '/async/organizations/habitat/projects/123/search/'
        assert actual == expected

        resolved = resolve(
            '/async/organizations/habitat/projects/123/search/')
        assert resolved.func.__name__ == async.Search.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123'

    def test_search_export(self):
        actual = reverse('async:search:export',
                         kwargs={
                            'organization': 'habitat',
                            'project': '123',
                         })
        expected = '/async/organizations/habitat/projects/123/search/export/'
        assert actual == expected

        resolved = resolve(
            '/async/organizations/habitat/projects/123/search/export/')
        assert resolved.func.__name__ == async.SearchExport.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123'
