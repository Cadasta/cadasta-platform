from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from ..views import default


class RessourceUrlTest(TestCase):
    def test_project_resource_list(self):
        url = reverse('resources:project_list',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert url == '/organizations/org-slug/projects/proj-slug/resources/'

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/resources/')
        assert resolved.func.__name__ == default.ProjectResources.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_project_resource_add_new(self):
        url = reverse('resources:project_add_new',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert url == ('/organizations/org-slug/projects/proj-slug/resources/'
                       'add/new/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/resources/add/new/')
        assert resolved.func.__name__ == default.ProjectResourcesNew.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_project_resource_add_exisiting(self):
        url = reverse('resources:project_add_existing',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert url == ('/organizations/org-slug/projects/proj-slug/resources/'
                       'add/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/resources/add/')
        assert resolved.func.__name__ == default.ProjectResourcesAdd.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_project_resource_detail(self):
        url = reverse('resources:project_detail',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'resource': 'abc123'})
        assert url == ('/organizations/org-slug/projects/proj-slug/resources/'
                       'abc123/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/resources/abc123/')
        assert (resolved.func.__name__ ==
                default.ProjectResourcesDetail.__name__)
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['resource'] == 'abc123'

    def test_project_resource_edit(self):
        url = reverse('resources:project_edit',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'resource': 'abc123'})
        assert url == ('/organizations/org-slug/projects/proj-slug/resources/'
                       'abc123/edit/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/resources/abc123/'
            'edit/')
        assert resolved.func.__name__ == default.ProjectResourcesEdit.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['resource'] == 'abc123'

    def test_project_resource_archive(self):
        url = reverse('resources:archive',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'resource': 'abc123'})
        assert url == ('/organizations/org-slug/projects/proj-slug/resources/'
                       'abc123/archive/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/resources/abc123/'
            'archive/')
        assert (resolved.func.__name__ ==
                default.ResourceArchive.__name__)
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['resource'] == 'abc123'

    def test_project_resource_unarchive(self):
        url = reverse('resources:unarchive',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'resource': 'abc123'})
        assert url == ('/organizations/org-slug/projects/proj-slug/resources/'
                       'abc123/unarchive/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/resources/abc123/'
            'unarchive/')
        assert (resolved.func.__name__ ==
                default.ResourceUnarchive.__name__)
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['resource'] == 'abc123'
