from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from core.tests.utils.urls import version_ns, version_url

from ..views import api


class SearchUrlTest(TestCase):
    def test_search(self):
        actual = reverse(
            version_ns('search:search'),
            kwargs={
                'organization': 'habitat',
                'project': '123abc',
            }
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/search/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/search/'))
        assert resolved.func.__name__ == api.Search.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
