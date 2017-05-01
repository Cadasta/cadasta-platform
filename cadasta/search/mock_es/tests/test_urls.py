from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from .. import views


class MockEsUrlsTest(TestCase):

    def test_search(self):
        actual = reverse('mock_es:search',
                         kwargs={
                            'projectid': '123abc',
                            'type': '456def',
                         })
        expected = '/project-123abc/456def/_search/'
        assert actual == expected

        resolved = resolve('/project-123abc/456def/_search/')
        assert resolved.func.__name__ == views.Search.__name__
        assert resolved.kwargs['projectid'] == '123abc'
        assert resolved.kwargs['type'] == '456def'

    def test_dump(self):
        actual = reverse('mock_es:dump',
                         kwargs={
                            'projectid': '123abc',
                            'type': '456def',
                         })
        expected = '/project-123abc/456def/_data/'
        assert actual == expected

        resolved = resolve('/project-123abc/456def/_data/')
        assert resolved.func.__name__ == views.Dump.__name__
        assert resolved.kwargs['projectid'] == '123abc'
        assert resolved.kwargs['type'] == '456def'
