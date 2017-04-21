from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from ..views import default


class PartiesUrlsTest(TestCase):
    def test_parties_list(self):
        url = reverse('parties:list',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/parties/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/parties/')
        assert resolved.func.__name__ == default.PartiesList.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_parties_add(self):
        url = reverse('parties:add',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'parties/new/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/parties/new/')
        assert resolved.func.__name__ == default.PartiesAdd.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_parties_detail(self):
        url = reverse('parties:detail',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'party': 'abc123'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'parties/abc123/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/'
            'parties/abc123/')
        assert resolved.func.__name__ == default.PartiesDetail.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['party'] == 'abc123'

    def test_parties_edit(self):
        url = reverse('parties:edit',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'party': 'abc123'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'parties/abc123/edit/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/'
            'parties/abc123/edit/')
        assert resolved.func.__name__ == default.PartiesEdit.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['party'] == 'abc123'

    def test_parties_delete(self):
        url = reverse('parties:delete',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'party': 'abc123'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'parties/abc123/delete/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/'
            'parties/abc123/delete/')
        assert resolved.func.__name__ == default.PartiesDelete.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['party'] == 'abc123'


class PartyResourcesUrlsTest(TestCase):
    def test_resource_add_from_lib(self):
        url = reverse('parties:resource_add',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'party': 'abc123'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'parties/abc123/resources/add/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/parties/'
            'abc123/resources/add/')
        assert resolved.func.__name__ == default.PartyResourcesAdd.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['party'] == 'abc123'

    def test_resource_add_new(self):
        url = reverse('parties:resource_new',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'party': 'abc123'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/records/'
                'parties/abc123/resources/new/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/records/parties/'
            'abc123/resources/new/')
        assert resolved.func.__name__ == default.PartyResourcesNew.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['party'] == 'abc123'
