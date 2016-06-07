import json

from django.utils.translation import gettext as _
from django.http import QueryDict
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies

from core.tests.base_test_case import UserTestCase
from accounts.tests.factories import UserFactory
from .factories import OrganizationFactory, clause
from ..models import Organization, OrganizationRole
from ..views import api


class OrganizationListAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.view'], ['organization/*'])
            ]
        }
        policy = Policy.objects.create(
            name='test-policy',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.view'], ['organization/*']),
                clause('deny', ['org.view'], ['organization/unauthorized'])
            ]
        }
        policy = Policy.objects.create(name='deny', body=json.dumps(clauses))
        self.unauth_user = UserFactory.create()
        assign_user_policies(self.unauth_user, policy)

    def _get(self, user=None, query=None, status=None, length=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/'
        if query is not None:
            url += '?' + query
        request = APIRequestFactory().get(url)
        if query is not None:
            setattr(request, 'GET', QueryDict(query))
        force_authenticate(request, user=user)
        response = api.OrganizationList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if length is not None:
            assert len(content) == length
        return content

    def test_full_list(self):
        """
        It should return all organizations.
        """
        OrganizationFactory.create_batch(2)
        content = self._get(status=200, length=2)
        assert 'users' not in content[0]

    def test_list_only_one_organization_is_authorized(self):
        """
        It should return all authorized organizations.
        """
        OrganizationFactory.create_from_kwargs([{}, {'slug': 'unauthorized'}])
        content = self._get(user=self.unauth_user, status=200, length=1)
        print(content[0])
        assert content[0]['slug'] != 'unauthorized'

    def test_full_list_with_unauthorized_user(self):
        """
        It should return an empty organization list.
        """
        OrganizationFactory.create_batch(2)
        self._get(user=AnonymousUser(), status=200, length=0)

    def test_filter_active(self):
        """
        It should return only one archived organization.
        """
        OrganizationFactory.create_from_kwargs(
            [{'archived': True}, {'archived': False}]
        )
        content = self._get(query='archived=True', status=200, length=1)
        assert content[0]['archived'] is True

    def test_search_filter(self):
        """
        It should return only two matching organizations.
        """
        OrganizationFactory.create_from_kwargs([
            {'name': 'A Match'},
            {'description': 'something that matches'},
            {'name': 'Excluded'}
        ])
        content = self._get(query='search=match', status=200, length=2)
        assert not any([org['name'] == 'Excluded' for org in content])

    def test_ordering(self):
        OrganizationFactory.create_from_kwargs([
            {'name': 'A'}, {'name': 'C'}, {'name': 'B'}
        ])
        content = self._get(query='ordering=name', status=200, length=3)
        names = [org['name'] for org in content]
        assert(names == sorted(names))

    def test_reverse_ordering(self):
        OrganizationFactory.create_from_kwargs([
            {'name': 'A'}, {'name': 'C'}, {'name': 'B'}
        ])
        content = self._get(query='ordering=-name', status=200, length=3)
        names = [org['name'] for org in content]
        assert(names == sorted(names, reverse=True))


class OrganizationCreateAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
        clauses = {
            'clause': [
                clause('allow', ['org.*']),
                clause('allow', ['org.*'], ['organization/*'])
            ]
        }
        policy = Policy.objects.create(
            name='test-policy-1',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.view'], ['organization/*'])
            ]
        }
        policy = Policy.objects.create(
            name='test-policy-2',
            body=json.dumps(clauses))
        self.unauth_user = UserFactory.create()
        assign_user_policies(self.unauth_user, policy)

    def _post(self, data, user=None, status=None, count=None,
              check_admin=False):
        if user is None:
            user = self.user
        url = '/v1/organizations/'
        request = APIRequestFactory().post(url, data)
        force_authenticate(request, user=user)
        response = api.OrganizationList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if count is not None:
            assert Organization.objects.count() == count
        if check_admin:
            org = Organization.objects.get(pk=content['id'])
            assert OrganizationRole.objects.get(
                organization=org, user=user
            ).admin
        return content

    def test_create_valid_organization(self):
        data = {'name': 'Org Name', 'description': 'Org description'}
        self._post(data, status=201, count=1, check_admin=True)

    def test_create_invalid_organization(self):
        data = {'description': 'Org description'}
        content = self._post(data, status=400, count=0)
        assert content['name'][0] == 'This field is required.'

    def test_create_organization_with_unauthorized_user(self):
        data = {'name': 'new_org', 'description': 'Org description'}
        content = self._post(data, user=self.unauth_user, status=403, count=0)
        assert content['detail'] == PermissionDenied.default_detail


class OrganizationDetailAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = api.OrganizationDetail.as_view()

        clauses = {
            'clause': [
                clause('allow', ['org.*']),
                clause('allow', ['org.*'], ['organization/*'])
            ]
        }
        policy = Policy.objects.create(
            name='test-policy-1',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

        clauses = {
            'clause': [
                clause('allow', ['org.update'], ['organization/*']),
                clause('deny', ['org.archive'], ['organization/*'])
            ]
        }
        policy = Policy.objects.create(
            name='test-policy-2',
            body=json.dumps(clauses))
        self.unauth_user = UserFactory.create()
        assign_user_policies(self.unauth_user, policy)

    def _get(self, slug, user=None, status=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{slug}/'
        request = APIRequestFactory().get(url.format(slug=slug))
        force_authenticate(request, user=user)
        response = self.view(request, slug=slug).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        return content

    def _patch(self, slug, data, user=None, status=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{slug}/'
        request = APIRequestFactory().patch(url.format(slug=slug), data)
        force_authenticate(request, user=user)
        response = self.view(request, slug=slug).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        return content

    def test_get_organization(self):
        org = OrganizationFactory.create(slug='org')
        content = self._get(org.slug, status=200)
        assert content['id'] == org.id
        assert 'users' in content

    def test_get_organization_with_unauthorized_user(self):
        org = OrganizationFactory.create(slug='org')
        content = self._get(org.slug, user=AnonymousUser(), status=403)
        assert content['detail'] == PermissionDenied.default_detail

    def test_get_organization_that_does_not_exist(self):
        content = self._get('some-org', status=404)
        assert content['detail'] == "Organization not found."

    def test_valid_update(self):
        org = OrganizationFactory.create(slug='org')
        data = {'name': 'Org Name'}
        self._patch(org.slug, data, status=200)
        org.refresh_from_db()
        assert org.name == data.get('name')

    def test_update_with_unauthorized_user(self):
        org = OrganizationFactory.create(name='Org name', slug='org')
        data = {'name': 'Org Name'}
        self._patch(org.slug, data, user=AnonymousUser(), status=403)
        org.refresh_from_db()
        assert org.name == 'Org name'

    def test_invalid_update(self):
        org = OrganizationFactory.create(name='Org name', slug='org')
        data = {'name': ''}
        content = self._patch(org.slug, data, status=400)
        org.refresh_from_db()
        assert org.name == 'Org name'
        assert content['name'][0] == 'This field may not be blank.'

    def test_archive(self):
        org = OrganizationFactory.create(name='Org name', slug='org')
        data = {'archived': True}
        self._patch(org.slug, data, status=200)
        org.refresh_from_db()
        assert org.archived

    def test_archive_with_unauthorized_user(self):
        org = OrganizationFactory.create(slug='org')
        data = {'archived': True}
        self._patch(org.slug, data, user=self.unauth_user, status=403)
        org.refresh_from_db()
        assert not org.archived

    def test_unarchive(self):
        org = OrganizationFactory.create(slug='org', archived=True)
        data = {'archived': False}
        self._patch(org.slug, data, status=200)
        org.refresh_from_db()
        assert not org.archived

    def test_unarchive_unauthorized_user(self):
        org = OrganizationFactory.create(slug='org', archived=True)
        data = {'archived': False}
        self._patch(org.slug, data, user=self.unauth_user, status=403)
        org.refresh_from_db()
        assert org.archived


class OrganizationUsersAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = api.OrganizationUsers.as_view()

        clauses = {
            'clause': [
                clause('allow', ['org.*']),
                clause('allow', ['org.*', 'org.*.*'], ['organization/*'])
            ]
        }
        policy = Policy.objects.create(
            name='test-policy',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def _get(self, org, user=None, status=None, length=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{slug}/users/'
        request = APIRequestFactory().get(url.format(slug=org.slug))
        force_authenticate(request, user=user)
        response = self.view(request, slug=org.slug).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if length is not None:
            assert len(content) == length
        return content

    def _post(self, org_or_slug, data, user=None, status=None, count=None):
        if isinstance(org_or_slug, Organization):
            slug = org_or_slug.slug
        else:
            slug = org_or_slug
        if user is None:
            user = self.user
        url = '/v1/organizations/{slug}/users/'
        request = APIRequestFactory().post(url.format(slug=slug), data)
        force_authenticate(request, user=user)
        response = self.view(request, slug=slug).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if count is not None and isinstance(org_or_slug, Organization):
            assert org_or_slug.users.count() == count
        return content

    def create_normal_org(self):
        org_users = UserFactory.create_batch(2)
        return OrganizationFactory.create(add_users=org_users)

    def test_get_users(self):
        org = self.create_normal_org()
        other_user = UserFactory.create()
        content = self._get(org, status=200, length=2)
        assert other_user.username not in [u['username'] for u in content]

    def test_get_users_with_unauthorized_user(self):
        org = OrganizationFactory.create()
        content = self._get(org, user=AnonymousUser(), status=403)
        assert content['detail'] == PermissionDenied.default_detail

    def test_add_user(self):
        org = self.create_normal_org()
        new_user = UserFactory.create()
        self._post(org, {'username': new_user.username}, status=201, count=3)

    def test_add_user_with_unauthorized_user(self):
        org = self.create_normal_org()
        new_user = UserFactory.create()
        content = self._post(org, {'username': new_user.username},
                             user=AnonymousUser(), status=403, count=2)
        assert content['detail'] == PermissionDenied.default_detail

    def test_add_user_that_does_not_exist(self):
        org = self.create_normal_org()
        content = self._post(org, {'username': 'some_username'},
                             status=400, count=2)
        assert (_('User with username or email some_username does not exist')
                in content['username'])

    def test_add_user_to_organization_that_does_not_exist(self):
        new_user = UserFactory.create()
        content = self._post('some-org', {'username': new_user.username},
                             status=404)
        assert content['detail'] == _("Organization not found.")


class OrganizationUsersDetailAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = api.OrganizationUsersDetail.as_view()
        clauses = {
            'clause': [
                clause('allow', ['org.*']),
                clause('allow', ['org.*', 'org.*.*'], ['organization/*'])
            ]
        }
        policy = Policy.objects.create(
            name='test-policy',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def _get(self, org, username, user=None, status=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/users/{username}'
        request = APIRequestFactory().get(url.format(org=org.slug,
                                                     username=username))
        force_authenticate(request, user=user)
        response = self.view(request, slug=org.slug,
                             username=username).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        return content

    def _patch(self, org, username, data, status=None, count=None):
        url = '/v1/organizations/{org}/users/{username}'
        request = APIRequestFactory().patch(
            url.format(org=org.slug, username=username),
            data=data, format='json')
        force_authenticate(request, user=self.user)
        response = self.view(request, slug=org.slug,
                             username=username).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if count is not None:
            assert org.users.count() == count
        return content

    def _delete(self, org_or_slug, username, user=None,
                status=None, count=None):
        if isinstance(org_or_slug, Organization):
            slug = org_or_slug.slug
        else:
            slug = org_or_slug
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/users/{username}'
        request = APIRequestFactory().delete(url.format(org=slug,
                                                        username=username))
        force_authenticate(request, user=user)
        response = self.view(request, slug=slug, username=username).render()
        content = None
        if len(response.content) > 0:
            content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if count is not None and isinstance(org_or_slug, Organization):
            assert org_or_slug.users.count() == count
        return content

    def test_get_user(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])
        content = self._get(org, user.username, status=200)
        assert content['username'] == user.username

    def test_update_user(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])
        self._patch(org, user.username, data={'roles': {'admin': True}},
                    status=200, count=1)
        role = OrganizationRole.objects.get(organization=org, user=user)
        assert role.admin is True

    def test_remove_user(self):
        user = UserFactory.create()
        user_to_remove = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user, user_to_remove])
        self._delete(org, user_to_remove.username, status=204, count=1)
        assert user_to_remove not in org.users.all()

    def test_remove_with_unauthorized_user(self):
        user = UserFactory.create()
        user_to_remove = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user, user_to_remove])
        content = self._delete(org, user_to_remove.username,
                               user=AnonymousUser(), status=403, count=2)
        assert content['detail'] == PermissionDenied.default_detail

    def test_remove_user_that_does_not_exist(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])
        content = self._delete(org, 'some_username', status=404, count=1)
        assert content['detail'] == "User not found."

    def test_remove_user_from_organization_that_does_not_exist(self):
        user = UserFactory.create()
        content = self._delete('some-org', user.username, status=404)
        assert content['detail'] == "Organization not found."
