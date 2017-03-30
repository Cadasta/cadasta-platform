from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from core.tests.utils.urls import version_ns, version_url

from ..views import api


class OrganizationUrlTest(TestCase):
    def test_organization_list(self):
        assert (reverse(version_ns('organization:list')) ==
                version_url('/organizations/'))

        resolved = resolve(version_url('/organizations/'))
        assert resolved.func.__name__ == api.OrganizationList.__name__

    def test_organization_detail(self):
        assert (reverse(version_ns('organization:detail'),
                        kwargs={'organization': 'org-slug'}) ==
                version_url('/organizations/org-slug/'))

        resolved = resolve(version_url('/organizations/org-slug/'))
        assert resolved.func.__name__ == api.OrganizationDetail.__name__
        assert resolved.kwargs['organization'] == 'org-slug'

    def test_organization_users(self):
        assert (reverse(version_ns('organization:users'),
                        kwargs={'organization': 'org-slug'}) ==
                version_url('/organizations/org-slug/users/'))

        resolved = resolve(version_url('/organizations/org-slug/users/'))
        assert resolved.func.__name__ == api.OrganizationUsers.__name__
        assert resolved.kwargs['organization'] == 'org-slug'

    def test_organization_users_detail(self):
        assert (reverse(version_ns('organization:users_detail'),
                        kwargs={'organization': 'org-slug',
                                'username': 'n_smith'}) ==
                version_url('/organizations/org-slug/users/n_smith/'))

        assert (reverse(version_ns('organization:users_detail'),
                        kwargs={'organization': 'org-slug',
                                'username': 'n_smith-@+.'}) ==
                version_url('/organizations/org-slug/users/n_smith-@+./'))

        resolved = resolve(
            version_url('/organizations/org-slug/users/n_smith/'))

        assert resolved.func.__name__ == api.OrganizationUsersDetail.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['username'] == 'n_smith'

        resolved = resolve(
            version_url('/organizations/org-slug/users/n_smith-@+./'))

        assert resolved.func.__name__ == api.OrganizationUsersDetail.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['username'] == 'n_smith-@+.'


class ProjectUrlTest(TestCase):

    def test_project_list(self):
        self.assertEqual(
            reverse(version_ns('project:list')),
            version_url('/projects/')
        )

        resolved = resolve(version_url('/projects/'))
        self.assertEqual(
            resolved.func.__name__,
            api.ProjectList.__name__)

    def test_organization_project_list(self):
        actual = reverse(
            version_ns('organization:project_list'),
            kwargs={'organization': 'habitat'}
        )

        expected = version_url('/organizations/habitat/projects/')

        assert actual == expected

        resolved = resolve(version_url('/organizations/habitat/projects/'))
        assert resolved.func.__name__ == api.OrganizationProjectList.__name__
        assert resolved.kwargs['organization'] == 'habitat'

    def test_project_users(self):
        actual = reverse(
            version_ns('organization:project_users'),
            kwargs={'organization': 'habitat', 'project': '123abc'}
        )
        expected = version_url('/organizations/habitat/projects/123abc/users/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/users/'))
        assert resolved.func.__name__ == api.ProjectUsers.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'

    def test_project_users_detail(self):
        actual = reverse(
            version_ns('organization:project_users_detail'),
            kwargs={'organization': 'habitat',
                    'project': '123abc',
                    'username': 'barbara'}
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/users/barbara/')
        assert actual == expected

        actual = reverse(
            version_ns('organization:project_users_detail'),
            kwargs={'organization': 'habitat',
                    'project': '123abc',
                    'username': 'barbara-@+.'}
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/users/barbara-@+./')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/users/barbara/'))
        assert resolved.func.__name__ == api.ProjectUsersDetail.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
        assert resolved.kwargs['username'] == 'barbara'

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/users/barbara-@+./'))
        assert resolved.func.__name__ == api.ProjectUsersDetail.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
        assert resolved.kwargs['username'] == 'barbara-@+.'


class UserUrlsTest(TestCase):
    def test_user_list(self):
        actual = reverse(version_ns('user:list'))
        expected = version_url('/users/')
        assert actual == expected

        resolved = resolve(version_url('/users/'))
        assert resolved.func.__name__ == api.UserAdminList.__name__

    def test_user_detail(self):
        actual = reverse(version_ns('user:detail'),
                         kwargs={'username': 'user-name'})

        expected = version_url('/users/user-name/')
        assert actual == expected

        resolved = resolve(version_url('/users/user-name/'))
        assert resolved.func.__name__ == api.UserAdminDetail.__name__
        assert resolved.kwargs['username'] == 'user-name'
