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

    def test_organization_unarchive(self):
        url = reverse('organization:unarchive', kwargs={'slug': 'org-slug'})
        assert (url == '/organizations/org-slug/unarchive/')

        resolved = resolve('/organizations/org-slug/unarchive/')
        assert resolved.func.__name__ == default.OrganizationUnarchive.__name__
        assert resolved.kwargs['slug'] == 'org-slug'

    def test_organization_project_add(self):
        url = reverse('organization:project-add',
                      kwargs={'organization': 'org-slug'})
        assert (url == '/organizations/org-slug/projects/new/')

        resolved = resolve('/organizations/org-slug/projects/new/')
        assert resolved.func.__name__ == default.ProjectAddWizard.__name__
        assert resolved.kwargs['organization'] == 'org-slug'


class UserUrlsTest(TestCase):
    def test_user_list(self):
        assert reverse('user:list') == '/users/'

        resolved = resolve('/users/')
        assert resolved.func.__name__ == default.UserList.__name__

    def test_user_activate(self):
        url = reverse('user:activate', kwargs={'user': 'user-name'})
        assert (url == '/users/user-name/activate/')

        url = reverse('user:activate', kwargs={'user': 'user-name-with-+@.'})
        assert (url == '/users/user-name-with-+@./activate/')

        resolved = resolve('/users/user-name/activate/')
        assert resolved.func.__name__ == default.UserActivation.__name__
        assert resolved.kwargs['user'] == 'user-name'
        assert resolved.func.view_initkwargs['new_state'] is True

        resolved = resolve('/users/user-name-with-+@./activate/')
        assert resolved.func.__name__ == default.UserActivation.__name__
        assert resolved.kwargs['user'] == 'user-name-with-+@.'
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
                              'project': 'proj-slug'})
        assert (url == '/organizations/org-slug/projects/proj-slug/')

        resolved = resolve('/organizations/org-slug/projects/proj-slug/')
        assert resolved.func.__name__ == default.ProjectMap.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_project_edit_geometry(self):
        url = reverse('organization:project-edit-geometry',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert (url == '/organizations/org-slug/projects/proj-slug'
                       '/edit/geometry/')

        resolved = resolve('/organizations/org-slug/projects/proj-slug'
                           '/edit/geometry/')
        assert resolved.func.__name__ == default.ProjectEditGeometry.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_project_edit_details(self):
        url = reverse('organization:project-edit-details',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert (url == '/organizations/org-slug/projects/proj-slug'
                       '/edit/details/')

        resolved = resolve('/organizations/org-slug/projects/proj-slug'
                           '/edit/details/')
        assert resolved.func.__name__ == default.ProjectEditDetails.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_project_edit_permissions(self):
        url = reverse('organization:project-edit-permissions',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert (url == '/organizations/org-slug/projects/proj-slug'
                       '/edit/permissions/')

        resolved = resolve('/organizations/org-slug/projects/proj-slug'
                           '/edit/permissions/')
        assert (resolved.func.__name__ ==
                default.ProjectEditPermissions.__name__)
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_project_archive(self):
        url = reverse('organization:project-archive',
                      kwargs={'organization': 'org-slug', 'project': 'prj'})
        assert (url == '/organizations/org-slug/projects/prj/archive/')

        resolved = resolve('/organizations/org-slug/projects/prj/archive/')
        assert resolved.func.__name__ == default.ProjectArchive.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'prj'

    def test_project_unarchive(self):
        url = reverse('organization:project-unarchive',
                      kwargs={'organization': 'org-slug', 'project': 'prj'})
        assert (url == '/organizations/org-slug/projects/prj/unarchive/')

        resolved = resolve('/organizations/org-slug/projects/prj/unarchive/')
        assert resolved.func.__name__ == default.ProjectUnarchive.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'prj'

    def test_project_download(self):
        url = reverse('organization:project-download',
                      kwargs={'organization': 'org-slug', 'project': 'prj'})
        assert (url == '/organizations/org-slug/projects/prj/download/')

        resolved = resolve('/organizations/org-slug/projects/prj/download/')
        assert resolved.func.__name__ == default.ProjectDataDownload.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'prj'


class OrganizationMembersUrlsTest(TestCase):
    def test_member_list(self):
        url = reverse('organization:members', kwargs={'slug': 'org-slug'})
        assert url == '/organizations/org-slug/members/'

        resolved = resolve('/organizations/org-slug/members/')
        assert resolved.func.__name__ == default.OrganizationMembers.__name__
        assert resolved.kwargs['slug'] == 'org-slug'

    def test_member_add(self):
        url = reverse('organization:members_add', kwargs={'slug': 'org-slug'})
        assert url == '/organizations/org-slug/members/add/'

        resolved = resolve('/organizations/org-slug/members/add/')
        assert (resolved.func.__name__ ==
                default.OrganizationMembersAdd.__name__)
        assert resolved.kwargs['slug'] == 'org-slug'

    def test_member_edit(self):
        url = reverse(
            'organization:members_edit',
            kwargs={'slug': 'org-slug', 'username': 'some-user'}
        )
        assert url == '/organizations/org-slug/members/some-user/'

        url = reverse(
            'organization:members_edit',
            kwargs={'slug': 'org-slug', 'username': 'some-user-with-+@.'}
        )
        assert url == '/organizations/org-slug/members/some-user-with-+@./'

        resolved = resolve('/organizations/org-slug/members/some-user/')
        assert (resolved.func.__name__ ==
                default.OrganizationMembersEdit.__name__)
        assert resolved.kwargs['slug'] == 'org-slug'
        assert resolved.kwargs['username'] == 'some-user'

        resolved = resolve(
            '/organizations/org-slug/members/some-user-with-+@./'
        )
        assert (resolved.func.__name__ ==
                default.OrganizationMembersEdit.__name__)
        assert resolved.kwargs['slug'] == 'org-slug'
        assert resolved.kwargs['username'] == 'some-user-with-+@.'

    def test_member_remove(self):
        url = reverse(
            'organization:members_remove',
            kwargs={'slug': 'org-slug', 'username': 'some-user'}
        )
        assert url == '/organizations/org-slug/members/some-user/remove/'

        url = reverse(
            'organization:members_remove',
            kwargs={'slug': 'org-slug', 'username': 'some-user-with-+@.'}
        )
        assert (url ==
                '/organizations/org-slug/members/some-user-with-+@./remove/')

        resolved = resolve('/organizations/org-slug/members/some-user/remove/')
        assert (resolved.func.__name__ ==
                default.OrganizationMembersRemove.__name__)
        assert resolved.kwargs['slug'] == 'org-slug'
        assert resolved.kwargs['username'] == 'some-user'

        resolved = resolve(
            '/organizations/org-slug/members/some-user-with-+@./remove/'
        )
        assert (resolved.func.__name__ ==
                default.OrganizationMembersRemove.__name__)
        assert resolved.kwargs['slug'] == 'org-slug'
        assert resolved.kwargs['username'] == 'some-user-with-+@.'
