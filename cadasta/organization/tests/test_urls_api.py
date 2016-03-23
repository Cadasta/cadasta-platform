from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from core.tests.url_utils import version_ns, version_url

from ..views import api


class OrganizationUrlTest(TestCase):
    def test_organization_list(self):
        self.assertEqual(
            reverse(version_ns('organization:list')),
            version_url('/organizations/')
        )

        resolved = resolve(version_url('/organizations/'))
        self.assertEqual(
            resolved.func.__name__,
            api.OrganizationList.__name__)

    def test_organization_detail(self):
        self.assertEqual(
            reverse(
                version_ns('organization:detail'),
                kwargs={'slug': 'org-slug'}),
            version_url('/organizations/org-slug/')
        )

        resolved = resolve(version_url('/organizations/org-slug/'))
        self.assertEqual(
            resolved.func.__name__,
            api.OrganizationDetail.__name__)
        self.assertEqual(resolved.kwargs['slug'], 'org-slug')

    def test_organization_users(self):
        self.assertEqual(
            reverse(
                version_ns('organization:users'),
                kwargs={'slug': 'org-slug'}),
            version_url('/organizations/org-slug/users/')
        )

        resolved = resolve(version_url('/organizations/org-slug/users/'))
        self.assertEqual(
            resolved.func.__name__,
            api.OrganizationUsers.__name__)
        self.assertEqual(resolved.kwargs['slug'], 'org-slug')

    def test_organization_users_detail(self):
        self.assertEqual(
            reverse(version_ns('organization:users_detail'),
                    kwargs={
                        'slug': 'org-slug',
                        'username': 'n_smith'
                    }),
            version_url('/organizations/org-slug/users/n_smith/')
        )

        resolved = resolve(
            version_url('/organizations/org-slug/users/n_smith/'))

        self.assertEqual(
            resolved.func.__name__,
            api.OrganizationUsersDetail.__name__)
        self.assertEqual(resolved.kwargs['slug'], 'org-slug')
        self.assertEqual(resolved.kwargs['username'], 'n_smith')


class ProjectUrlTest(TestCase):
    def test_project_list(self):
        actual = reverse(
            version_ns('organization:project_list'),
            kwargs={'slug': 'habitat'}
        )

        expected = version_url('/organizations/habitat/projects/')

        assert actual == expected

        resolved = resolve(version_url('/organizations/habitat/projects/'))
        assert resolved.func.__name__ == api.ProjectList.__name__
        assert resolved.kwargs['slug'] == 'habitat'

    def test_project_users(self):
        actual = reverse(
            version_ns('organization:project_users'),
            kwargs={'slug': 'habitat', 'project_id': '123abc'}
        )
        expected = version_url('/organizations/habitat/projects/123abc/users/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/users/'))
        assert resolved.func.__name__ == api.ProjectUsers.__name__
        assert resolved.kwargs['slug'] == 'habitat'
        assert resolved.kwargs['project_id'] == '123abc'

    def test_project_users_detail(self):
        actual = reverse(
            version_ns('organization:project_users_detail'),
            kwargs={'slug': 'habitat',
                    'project_id': '123abc',
                    'username': 'barbara'}
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/users/barbara/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/users/barbara/'))
        assert resolved.func.__name__ == api.ProjectUsersDetail.__name__
        assert resolved.kwargs['slug'] == 'habitat'
        assert resolved.kwargs['project_id'] == '123abc'
        assert resolved.kwargs['username'] == 'barbara'
