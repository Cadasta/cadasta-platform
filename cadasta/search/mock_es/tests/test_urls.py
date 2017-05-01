from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from .. import views


class MockEsUrlsTest(TestCase):

    def test_all(self):
        actual = reverse('mock_es:all',
                         kwargs={
                            'projectid': '123abc',
                         })
        expected = '/project-123abc/_search/'
        assert actual == expected

        resolved = resolve('/project-123abc/_search/')
        assert resolved.func.__name__ == views.AllEsTypes.__name__
        assert resolved.kwargs['projectid'] == '123abc'

    def test_type(self):
        actual = reverse('mock_es:type',
                         kwargs={
                            'projectid': 'foo',
                            'type': 'bar',
                         })
        expected = '/project-foo/bar/_search/'
        assert actual == expected

        resolved = resolve('/project-foo/bar/_search/')
        assert resolved.func.__name__ == views.SingleEsType.__name__
        assert resolved.kwargs['projectid'] == 'foo'
        assert resolved.kwargs['type'] == 'bar'

    def test_dump_all(self):
        actual = reverse('mock_es:dump_all',
                         kwargs={
                            'projectid': '123abc',
                         })
        expected = '/project-123abc/_data/'
        assert actual == expected

        resolved = resolve('/project-123abc/_data/')
        assert resolved.func.__name__ == views.DumpAllEsTypes.__name__
        assert resolved.kwargs['projectid'] == '123abc'
