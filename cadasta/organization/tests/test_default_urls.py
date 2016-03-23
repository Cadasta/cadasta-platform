from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from ..views import default


class OrganizationUrlsTest(TestCase):
    def test_organization_list(self):
        assert reverse('organization:list') == '/organizations/'

        resolved = resolve('/organizations/')
        assert resolved.func.__name__ == default.OrganizationList.__name__

    def test_organization_add(self):
        assert reverse('organization:add') == '/organizations/new/'

        resolved = resolve('/organizations/new/')
        assert resolved.func.__name__ == default.OrganizationAdd.__name__

    def test_organization_dashboard(self):
        url = reverse('organization:dashboard', kwargs={'slug': 'org-slug'})
        assert (url == '/organizations/org-slug/')

        resolved = resolve('/organizations/org-slug/')
        assert resolved.func.__name__ == default.OrganizationDashboard.__name__
        assert resolved.kwargs['slug'] == 'org-slug'

    def test_organization_edit(self):
        url = reverse('organization:edit', kwargs={'slug': 'org-slug'})
        assert (url == '/organizations/org-slug/edit/')

        resolved = resolve('/organizations/org-slug/edit/')
        assert resolved.func.__name__ == default.OrganizationEdit.__name__
        assert resolved.kwargs['slug'] == 'org-slug'

    def test_organization_archive(self):
        url = reverse('organization:archive', kwargs={'slug': 'org-slug'})
        assert (url == '/organizations/org-slug/archive/')

        resolved = resolve('/organizations/org-slug/archive/')
        assert resolved.func.__name__ == default.OrganizationArchive.__name__
        assert resolved.kwargs['slug'] == 'org-slug'


class UserUrlsTest(TestCase):
    def test_user_list(self):
        assert reverse('user:list') == '/users/'

        resolved = resolve('/users/')
        assert resolved.func.__name__ == default.UserList.__name__

    def test_user_activate(self):
        url = reverse('user:activate', kwargs={'user': 'user-name'})
        assert (url == '/users/user-name/activate/')

        resolved = resolve('/users/user-name/activate/')
        assert resolved.func.__name__ == default.UserActivation.__name__
        assert resolved.kwargs['user'] == 'user-name'
        assert resolved.func.view_initkwargs['new_state'] is True

    def test_user_deactivate(self):
        url = reverse('user:deactivate', kwargs={'user': 'user-name'})
        assert (url == '/users/user-name/deactivate/')

        resolved = resolve('/users/user-name/deactivate/')
        assert resolved.func.__name__ == default.UserActivation.__name__
        assert resolved.kwargs['user'] == 'user-name'
        assert resolved.func.view_initkwargs['new_state'] is False


class ProjectUrlsTest(TestCase):
    def test_project_list(self):
        assert reverse('project:list') == '/projects/'

        resolved = resolve('/projects/')
        assert resolved.func.__name__ == default.ProjectList.__name__

    def test_project_add(self):
        assert reverse('project:add') == '/projects/new/'

        resolved = resolve('/projects/new/')
        assert resolved.func.__name__ == default.ProjectAddWizard.__name__

    def test_project_dashboard(self):
        url = reverse('organization:project-dashboard',
                      kwargs={'organization': 'org-slug',
                              'project':      'proj-slug'})
        assert (url == '/organizations/org-slug/projects/proj-slug/')

        resolved = resolve('/organizations/org-slug/projects/proj-slug/')
        assert resolved.func.__name__ == default.ProjectDashboard.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_project_edit(self):
        url = reverse('organization:project-edit',
                      kwargs={'organization': 'org-slug',
                              'project':      'proj-slug'})
        assert (url == '/organizations/org-slug/projects/proj-slug/edit/')

        resolved = resolve('/organizations/org-slug/projects/proj-slug/edit/')
        assert resolved.func.__name__ == default.ProjectEdit.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
