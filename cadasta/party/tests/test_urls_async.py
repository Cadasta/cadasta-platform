from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from ..views import async


class PartyUrlTest(TestCase):
    def test_party_list(self):
        actual = reverse(
            'async:party:list',
            kwargs={
                'organization': 'habitat',
                'project': '123abc',
            }
        )
        expected = '/async/organizations/habitat/projects/123abc/parties/'
        assert actual == expected

        resolved = resolve(
            '/async/organizations/habitat/projects/123abc/parties/')
        assert resolved.func.__name__ == async.PartyList.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
