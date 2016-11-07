from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from ..views import default


class SearchUrlsTest(TestCase):
    def test_search(self):
        url = reverse('search:search',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert url == '/organizations/org-slug/projects/proj-slug/search/'

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/search/')
        assert resolved.func.__name__ == default.Search.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
