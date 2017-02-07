from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from ..views import async


class SearchUrlTest(TestCase):
    def test_search(self):
        actual = reverse('async:search:search',
                         kwargs={
                            'organization': 'habitat',
                            'project': '123abc',
                         })
        expected = '/async/organizations/habitat/projects/123abc/search/'
        assert actual == expected

        resolved = resolve(
            '/async/organizations/habitat/projects/123abc/search/')
        assert resolved.func.__name__ == async.Search.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
